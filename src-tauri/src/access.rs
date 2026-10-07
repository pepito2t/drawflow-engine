use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use argon2::password_hash::rand_core::OsRng;
use argon2::password_hash::{PasswordHash, PasswordHasher, PasswordVerifier, SaltString};
use argon2::Argon2;
use serde::{Deserialize, Serialize};
use subtle::ConstantTimeEq;
use tauri::{AppHandle, Manager, State};

use crate::error::BridgeError;
use crate::integrations::protocol::ServerMessage;
use crate::integrations::IntegrationState;
use crate::paths::write_atomically;

const ACCESS_FILE_NAME: &str = "access-code.json";
const DEFAULT_ACCESS_CODE: &str = "0000";
const MIN_CODE_LENGTH: usize = 4;
const MAX_CODE_LENGTH: usize = 12;
const FREE_ATTEMPTS: u32 = 3;
const MAX_DELAY_SECONDS: u64 = 300;

#[derive(Serialize, Deserialize)]
struct StoredCode {
    hash: String,
}

#[derive(Clone, Debug, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LockStatus {
    required: bool,
    unlocked: bool,
}

/// Escalating delay after repeated wrong codes, measured from the last failure.
#[derive(Default)]
struct AttemptPolicy {
    failures: u32,
    blocked_until: Option<Instant>,
}

impl AttemptPolicy {
    fn remaining_block(&self, now: Instant) -> Option<Duration> {
        self.blocked_until
            .and_then(|until| until.checked_duration_since(now))
            .filter(|remaining| !remaining.is_zero())
    }

    fn record_failure(&mut self, now: Instant) {
        self.failures += 1;
        if self.failures >= FREE_ATTEMPTS {
            let exponent = (self.failures - FREE_ATTEMPTS).min(16);
            let seconds = (1u64 << exponent).min(MAX_DELAY_SECONDS);
            self.blocked_until = Some(now + Duration::from_secs(seconds));
        }
    }

    fn reset(&mut self) {
        *self = Self::default();
    }
}

#[derive(Default)]
struct LockState {
    unlocked: bool,
    attempts: AttemptPolicy,
}

#[derive(Default)]
pub struct AccessLock(Mutex<LockState>);

impl AccessLock {
    pub fn ensure_unlocked(&self) -> Result<(), BridgeError> {
        if !lock_required() || self.state()?.unlocked {
            return Ok(());
        }
        Err(BridgeError::Locked)
    }

    fn state(&self) -> Result<std::sync::MutexGuard<'_, LockState>, BridgeError> {
        self.0.lock().map_err(|_| BridgeError::StatePoisoned)
    }
}

/// Development builds never ask for the code.
fn lock_required() -> bool {
    cfg!(not(debug_assertions))
}

#[tauri::command]
pub fn lock_status(lock: State<'_, AccessLock>) -> Result<LockStatus, BridgeError> {
    Ok(LockStatus {
        required: lock_required(),
        unlocked: !lock_required() || lock.state()?.unlocked,
    })
}

/// Argon2 verification runs off the main thread; the lock is held only around the state updates.
#[tauri::command(async)]
pub async fn unlock(
    app: AppHandle,
    lock: State<'_, AccessLock>,
    code: String,
) -> Result<(), BridgeError> {
    if let Some(remaining) = lock.state()?.attempts.remaining_block(Instant::now()) {
        return Err(BridgeError::TooManyAttempts(remaining.as_secs().max(1)));
    }
    let path = access_file(&app)?;
    let accepted =
        tauri::async_runtime::spawn_blocking(move || verify_code(&path, &code)).await??;
    let mut state = lock.state()?;
    if accepted {
        state.attempts.reset();
        state.unlocked = true;
        app.state::<IntegrationState>()
            .broadcast(&ServerMessage::Locked { locked: false });
        return Ok(());
    }
    state.attempts.record_failure(Instant::now());
    Err(BridgeError::WrongAccessCode)
}

#[tauri::command(async)]
pub async fn change_access_code(
    app: AppHandle,
    lock: State<'_, AccessLock>,
    current: String,
    new_code: String,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    let path = access_file(&app)?;
    tauri::async_runtime::spawn_blocking(move || replace_code(&path, &current, &new_code)).await?
}

fn replace_code(path: &Path, current: &str, new_code: &str) -> Result<(), BridgeError> {
    if !verify_code(path, current)? {
        return Err(BridgeError::WrongAccessCode);
    }
    validate_code(new_code)?;
    write_code(path, &hash_code(new_code)?)
}

fn access_file(app: &AppHandle) -> Result<PathBuf, BridgeError> {
    Ok(app.path().app_config_dir()?.join(ACCESS_FILE_NAME))
}

fn verify_code(path: &Path, code: &str) -> Result<bool, BridgeError> {
    let Some(stored) = read_stored(path)? else {
        return Ok(code.as_bytes().ct_eq(DEFAULT_ACCESS_CODE.as_bytes()).into());
    };
    let hash = PasswordHash::new(&stored.hash).map_err(|_| BridgeError::AccessFileCorrupted)?;
    Ok(Argon2::default()
        .verify_password(code.as_bytes(), &hash)
        .is_ok())
}

fn validate_code(code: &str) -> Result<(), BridgeError> {
    let length_ok = (MIN_CODE_LENGTH..=MAX_CODE_LENGTH).contains(&code.len());
    if length_ok && code.chars().all(|character| character.is_ascii_digit()) {
        return Ok(());
    }
    Err(BridgeError::InvalidAccessCode {
        min: MIN_CODE_LENGTH,
        max: MAX_CODE_LENGTH,
    })
}

fn hash_code(code: &str) -> Result<String, BridgeError> {
    let salt = SaltString::generate(&mut OsRng);
    Argon2::default()
        .hash_password(code.as_bytes(), &salt)
        .map(|hash| hash.to_string())
        .map_err(|_| BridgeError::AccessHashing)
}

fn read_stored(path: &Path) -> Result<Option<StoredCode>, BridgeError> {
    if !path.exists() {
        return Ok(None);
    }
    let content = fs::read_to_string(path).map_err(BridgeError::AccessFile)?;
    serde_json::from_str(&content)
        .map(Some)
        .map_err(|_| BridgeError::AccessFileCorrupted)
}

fn write_code(path: &Path, hash: &str) -> Result<(), BridgeError> {
    let stored = StoredCode {
        hash: hash.to_owned(),
    };
    let content = serde_json::to_vec(&stored)?;
    write_atomically(path, &content).map_err(BridgeError::AccessFile)
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    #[test]
    fn default_code_is_0000_until_changed() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join(ACCESS_FILE_NAME);
        assert!(verify_code(&path, "0000").unwrap());
        assert!(!verify_code(&path, "1234").unwrap());
    }

    #[test]
    fn changed_code_is_stored_hashed_and_verifiable() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join("Réglages é").join(ACCESS_FILE_NAME);
        write_code(&path, &hash_code("482913").unwrap()).unwrap();
        let content = fs::read_to_string(&path).unwrap();
        assert!(!content.contains("482913"));
        assert!(content.contains("$argon2id$"));
        assert!(verify_code(&path, "482913").unwrap());
        assert!(!verify_code(&path, "0000").unwrap());
    }

    #[test]
    fn corrupted_file_is_reported() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join(ACCESS_FILE_NAME);
        fs::write(&path, "nope").unwrap();
        assert!(matches!(
            verify_code(&path, "0000"),
            Err(BridgeError::AccessFileCorrupted)
        ));
    }

    #[test]
    fn replacing_the_code_requires_the_current_one() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join(ACCESS_FILE_NAME);
        assert!(matches!(
            replace_code(&path, "1111", "2222"),
            Err(BridgeError::WrongAccessCode)
        ));
        replace_code(&path, "0000", "2222").unwrap();
        assert!(verify_code(&path, "2222").unwrap());
    }

    #[test]
    fn codes_must_be_4_to_12_digits() {
        assert!(validate_code("0420").is_ok());
        assert!(validate_code("123456789012").is_ok());
        assert!(validate_code("123").is_err());
        assert!(validate_code("12ab").is_err());
        assert!(validate_code("1234567890123").is_err());
    }

    #[test]
    fn delay_starts_after_free_attempts_and_grows() {
        let mut policy = AttemptPolicy::default();
        let now = Instant::now();
        policy.record_failure(now);
        policy.record_failure(now);
        assert!(policy.remaining_block(now).is_none());
        policy.record_failure(now);
        assert_eq!(policy.remaining_block(now), Some(Duration::from_secs(1)));
        policy.record_failure(now);
        assert_eq!(policy.remaining_block(now), Some(Duration::from_secs(2)));
        assert!(policy
            .remaining_block(now + Duration::from_secs(3))
            .is_none());
    }

    #[test]
    fn delay_is_capped() {
        let mut policy = AttemptPolicy::default();
        let now = Instant::now();
        for _ in 0..40 {
            policy.record_failure(now);
        }
        assert_eq!(
            policy.remaining_block(now),
            Some(Duration::from_secs(MAX_DELAY_SECONDS))
        );
    }

    #[test]
    fn success_resets_attempts() {
        let mut policy = AttemptPolicy::default();
        let now = Instant::now();
        for _ in 0..5 {
            policy.record_failure(now);
        }
        policy.reset();
        assert!(policy.remaining_block(now).is_none());
    }
}
