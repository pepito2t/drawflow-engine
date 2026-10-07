//! Watched folders: a file that lands in a folder launches a preset through the UI's named commands.

use std::collections::HashSet;
use std::fs;
use std::io::Read;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use notify::{Config, Event, EventKind, PollWatcher, RecommendedWatcher, RecursiveMode, Watcher};
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use tauri::{AppHandle, Manager, State};

use crate::access::AccessLock;
use crate::bounded_set::BoundedSet;
use crate::error::BridgeError;
use crate::integrations::{dispatch_to_ui, protocol::CommandRequest};
use crate::paths::write_atomically;

const CONFIG_FILE_NAME: &str = "automations.json";
const SEEN_FILE_NAME: &str = "automations-seen.json";
const RUN_COMMAND: &str = "automation.run";
const WATCHED_EXTENSIONS: [&str; 4] = ["dwg", "dxf", "pdf", "xlsx"];
// A plan copied over the network grows for a while: wait until its size stops changing.
const STABLE_FOR: Duration = Duration::from_secs(2);
const STABLE_POLL: Duration = Duration::from_millis(500);
const STABLE_TIMEOUT: Duration = Duration::from_secs(300);
const POLL_INTERVAL: Duration = Duration::from_secs(5);
const RETRY_DELAY: Duration = Duration::from_secs(20);
const MAX_ATTEMPTS: u32 = 15;
const MAX_SEEN: usize = 2000;
const HASH_BUFFER: usize = 1 << 20;
const UNC_PREFIX: &str = r"\\";

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Automation {
    pub id: String,
    pub folder: PathBuf,
    pub preset_id: String,
    pub enabled: bool,
}

#[derive(Clone, Debug, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct AutomationStatus {
    pub automations: Vec<Automation>,
    pub errors: Vec<String>,
}

type FolderWatcher = Box<dyn Watcher + Send>;

pub struct AutomationState {
    watchers: Mutex<Vec<FolderWatcher>>,
    errors: Mutex<Vec<String>>,
    pending: Mutex<HashSet<PathBuf>>,
    seen: Mutex<BoundedSet>,
}

impl Default for AutomationState {
    fn default() -> Self {
        Self {
            watchers: Mutex::default(),
            errors: Mutex::default(),
            pending: Mutex::default(),
            seen: Mutex::new(BoundedSet::new(MAX_SEEN)),
        }
    }
}

impl AutomationState {
    fn errors(&self) -> Vec<String> {
        self.errors
            .lock()
            .map(|errors| errors.clone())
            .unwrap_or_default()
    }

    fn claim(&self, path: &Path) -> bool {
        self.pending
            .lock()
            .map(|mut pending| pending.insert(path.to_path_buf()))
            .unwrap_or(false)
    }

    fn release(&self, path: &Path) {
        if let Ok(mut pending) = self.pending.lock() {
            pending.remove(path);
        }
    }

    /// Returns false when the fingerprint was already handled; remembers it otherwise.
    fn first_time(&self, fingerprint: &str) -> bool {
        self.seen
            .lock()
            .map(|mut seen| seen.insert(fingerprint.to_owned()))
            .unwrap_or(false)
    }
}

pub fn config_file(app: &AppHandle) -> Result<PathBuf, BridgeError> {
    Ok(app.path().app_config_dir()?.join(CONFIG_FILE_NAME))
}

/// A missing file means no automation; a corrupt one is reported, never silently emptied.
pub fn load(path: &Path) -> Result<Vec<Automation>, BridgeError> {
    let content = match fs::read_to_string(path) {
        Ok(content) => content,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(Vec::new()),
        Err(error) => return Err(BridgeError::AutomationsFile(error)),
    };
    serde_json::from_str(&content)
        .map_err(|_| BridgeError::ConfigCorrupted(CONFIG_FILE_NAME.to_owned()))
}

pub fn save(path: &Path, automations: &[Automation]) -> Result<(), BridgeError> {
    let content = serde_json::to_vec_pretty(automations)?;
    write_atomically(path, &content).map_err(BridgeError::AutomationsFile)
}

pub fn validate(automations: &[Automation]) -> Result<(), BridgeError> {
    for automation in automations {
        if automation.id.is_empty() || automation.preset_id.is_empty() {
            return Err(BridgeError::InvalidAutomation(
                "Chaque automatisation doit avoir un préréglage.".to_owned(),
            ));
        }
        if automation.enabled && !automation.folder.is_dir() {
            return Err(BridgeError::InvalidAutomation(format!(
                "Le dossier « {} » n'existe pas.",
                automation.folder.display()
            )));
        }
    }
    Ok(())
}

pub fn is_watched_file(path: &Path) -> bool {
    path.extension()
        .and_then(|extension| extension.to_str())
        .map(|extension| WATCHED_EXTENSIONS.contains(&extension.to_ascii_lowercase().as_str()))
        .unwrap_or(false)
}

/// Network shares rarely deliver change notifications: those folders are polled instead.
pub fn needs_polling(folder: &Path) -> bool {
    folder.to_string_lossy().starts_with(UNC_PREFIX)
}

fn watch(app: AppHandle, automation: Automation) -> Result<FolderWatcher, notify::Error> {
    let handler_app = app.clone();
    let handler_automation = automation.clone();
    let handler = move |result: notify::Result<Event>| {
        let Ok(event) = result else { return };
        if !matches!(event.kind, EventKind::Create(_) | EventKind::Modify(_)) {
            return;
        }
        for path in event.paths.into_iter().filter(|path| is_watched_file(path)) {
            schedule(handler_app.clone(), handler_automation.clone(), path);
        }
    };
    let polling = |handler: Box<dyn Fn(notify::Result<Event>) + Send>| {
        let config = Config::default().with_poll_interval(POLL_INTERVAL);
        let mut watcher = PollWatcher::new(handler, config)?;
        watcher.watch(&automation.folder, RecursiveMode::NonRecursive)?;
        Ok(Box::new(watcher) as FolderWatcher)
    };
    if needs_polling(&automation.folder) {
        return polling(Box::new(handler));
    }
    match RecommendedWatcher::new(handler.clone(), Config::default()) {
        Ok(mut watcher) => {
            watcher.watch(&automation.folder, RecursiveMode::NonRecursive)?;
            Ok(Box::new(watcher) as FolderWatcher)
        }
        Err(_) => polling(Box::new(handler)),
    }
}

fn schedule(app: AppHandle, automation: Automation, path: PathBuf) {
    let state = app.state::<AutomationState>();
    if !state.claim(&path) {
        return;
    }
    tauri::async_runtime::spawn(async move {
        handle_new_file(&app, &automation, &path).await;
        app.state::<AutomationState>().release(&path);
    });
}

async fn handle_new_file(app: &AppHandle, automation: &Automation, path: &Path) {
    let file = path.to_path_buf();
    let stabilized = tauri::async_runtime::spawn_blocking(move || {
        wait_until_stable(&file).and_then(|_| fingerprint_of(&file).ok())
    });
    let Ok(Some(fingerprint)) = stabilized.await else {
        return;
    };
    let state = app.state::<AutomationState>();
    if !state.first_time(&fingerprint) {
        return;
    }
    persist_seen(app);
    let request = CommandRequest {
        id: format!("automation-{}", &fingerprint[..12]),
        command: RUN_COMMAND.to_owned(),
        args: json!({ "automationId": automation.id, "path": path }),
    };
    for _ in 0..MAX_ATTEMPTS {
        let unlocked = app.state::<AccessLock>().ensure_unlocked().is_ok();
        if unlocked && dispatch_to_ui(app, request.clone()).await.ok {
            return;
        }
        tokio::time::sleep(RETRY_DELAY).await;
    }
}

/// Blocks until the file keeps the same size for STABLE_FOR and can be opened.
pub fn wait_until_stable(path: &Path) -> Option<u64> {
    let started = Instant::now();
    let mut last_size: Option<u64> = None;
    let mut unchanged_since = Instant::now();
    while started.elapsed() < STABLE_TIMEOUT {
        let size = fs::metadata(path).ok()?.len();
        if last_size != Some(size) {
            last_size = Some(size);
            unchanged_since = Instant::now();
        } else if unchanged_since.elapsed() >= STABLE_FOR && fs::File::open(path).is_ok() {
            return Some(size);
        }
        std::thread::sleep(STABLE_POLL);
    }
    None
}

pub fn fingerprint_of(path: &Path) -> std::io::Result<String> {
    let mut file = fs::File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buffer = vec![0u8; HASH_BUFFER];
    loop {
        let read = file.read(&mut buffer)?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

fn seen_file(app: &AppHandle) -> Result<PathBuf, BridgeError> {
    Ok(app.path().app_config_dir()?.join(SEEN_FILE_NAME))
}

fn load_seen(app: &AppHandle) {
    let Ok(path) = seen_file(app) else { return };
    let loaded: Vec<String> = fs::read_to_string(path)
        .ok()
        .and_then(|content| serde_json::from_str(&content).ok())
        .unwrap_or_default();
    if let Ok(mut seen) = app.state::<AutomationState>().seen.lock() {
        seen.extend(loaded);
    }
}

fn persist_seen(app: &AppHandle) {
    let state = app.state::<AutomationState>();
    let Ok(seen) = state.seen.lock() else {
        return;
    };
    let snapshot: Vec<&String> = seen.iter().collect();
    if let Ok(path) = seen_file(app) {
        if let Ok(content) = serde_json::to_vec(&snapshot) {
            // Losing this file only risks one duplicate run; not worth failing the launch.
            let _best_effort = fs::write(path, content);
        }
    }
}

pub fn apply(app: &AppHandle, automations: &[Automation]) {
    let mut watchers = Vec::new();
    let mut errors = Vec::new();
    for automation in automations.iter().filter(|automation| automation.enabled) {
        match watch(app.clone(), automation.clone()) {
            Ok(watcher) => watchers.push(watcher),
            Err(error) => errors.push(format!(
                "Surveillance impossible pour « {} » : {error}",
                automation.folder.display()
            )),
        }
    }
    let state = app.state::<AutomationState>();
    replace(&state.watchers, watchers);
    replace(&state.errors, errors);
}

fn replace<T>(slot: &Mutex<T>, value: T) {
    if let Ok(mut current) = slot.lock() {
        *current = value;
    }
}

/// A corrupt file must not keep the application from starting: nothing is watched and the
/// status reports why.
pub fn start_at_launch(app: &AppHandle) -> Result<(), BridgeError> {
    load_seen(app);
    match load(&config_file(app)?) {
        Ok(automations) => apply(app, &automations),
        Err(error) => replace(
            &app.state::<AutomationState>().errors,
            vec![error.to_string()],
        ),
    }
    Ok(())
}

#[tauri::command]
pub fn automation_status(
    app: AppHandle,
    state: State<'_, AutomationState>,
    lock: State<'_, AccessLock>,
) -> Result<AutomationStatus, BridgeError> {
    lock.ensure_unlocked()?;
    Ok(AutomationStatus {
        automations: load(&config_file(&app)?)?,
        errors: state.errors(),
    })
}

#[tauri::command]
pub fn automation_save(
    app: AppHandle,
    lock: State<'_, AccessLock>,
    automations: Vec<Automation>,
) -> Result<AutomationStatus, BridgeError> {
    lock.ensure_unlocked()?;
    validate(&automations)?;
    save(&config_file(&app)?, &automations)?;
    apply(&app, &automations);
    Ok(AutomationStatus {
        errors: app.state::<AutomationState>().errors(),
        automations,
    })
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    fn automation(folder: &Path) -> Automation {
        Automation {
            id: "a1".to_owned(),
            folder: folder.to_path_buf(),
            preset_id: "p1".to_owned(),
            enabled: true,
        }
    }

    #[test]
    fn config_round_trip_and_missing_file() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join("Réglages").join(CONFIG_FILE_NAME);
        assert!(load(&path).unwrap().is_empty());
        let automations = vec![automation(folder.path())];
        save(&path, &automations).unwrap();
        assert_eq!(load(&path).unwrap(), automations);
    }

    #[test]
    fn corrupt_config_is_an_error_not_an_empty_list() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join(CONFIG_FILE_NAME);
        fs::write(&path, "[ pas du json").unwrap();
        assert!(matches!(load(&path), Err(BridgeError::ConfigCorrupted(_))));
        assert_eq!(fs::read_to_string(&path).unwrap(), "[ pas du json");
    }

    #[test]
    fn only_plans_and_documents_are_watched() {
        assert!(is_watched_file(Path::new("C:/Plans/façade.DWG")));
        assert!(is_watched_file(Path::new("C:/Plans/offre.xlsx")));
        assert!(!is_watched_file(Path::new("C:/Plans/façade.dwg.tmp")));
        assert!(!is_watched_file(Path::new("C:/Plans/notes.txt")));
    }

    #[test]
    fn network_shares_are_polled() {
        assert!(needs_polling(Path::new(r"\\serveur\plans")));
        assert!(!needs_polling(Path::new(r"C:\Plans")));
    }

    #[test]
    fn validation_requires_a_preset_and_an_existing_folder() {
        let folder = tempfile::tempdir().unwrap();
        assert!(validate(&[automation(folder.path())]).is_ok());
        let mut missing = automation(&folder.path().join("absent"));
        assert!(validate(&[missing.clone()]).is_err());
        missing.enabled = false;
        assert!(validate(&[missing]).is_ok());
        let mut no_preset = automation(folder.path());
        no_preset.preset_id.clear();
        assert!(validate(&[no_preset]).is_err());
    }

    #[test]
    fn stable_file_is_fingerprinted_once() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join("plan.dxf");
        fs::write(&path, b"0\nSECTION\n").unwrap();
        assert_eq!(wait_until_stable(&path), Some(10));
        let state = AutomationState::default();
        let fingerprint = fingerprint_of(&path).unwrap();
        assert!(state.first_time(&fingerprint));
        assert!(!state.first_time(&fingerprint));
        assert!(wait_until_stable(&folder.path().join("absent.dxf")).is_none());
    }
}
