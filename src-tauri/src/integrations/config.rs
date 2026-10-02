use std::fs;
use std::path::{Path, PathBuf};

use argon2::password_hash::rand_core::{OsRng, RngCore};
use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Manager};

use crate::error::BridgeError;

const CONFIG_FILE_NAME: &str = "integrations.json";
pub const DEFAULT_PORT: u16 = 51717;
const TOKEN_BYTES: usize = 24;

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct IntegrationConfig {
    pub enabled: bool,
    pub port: u16,
    pub token: String,
}

impl IntegrationConfig {
    fn generated() -> Self {
        Self {
            enabled: false,
            port: DEFAULT_PORT,
            token: generate_token(),
        }
    }
}

pub fn config_file(app: &AppHandle) -> Result<PathBuf, BridgeError> {
    Ok(app.path().app_config_dir()?.join(CONFIG_FILE_NAME))
}

/// Missing or unreadable configuration yields a disabled default with a fresh token.
pub fn load(path: &Path) -> IntegrationConfig {
    fs::read_to_string(path)
        .ok()
        .and_then(|content| serde_json::from_str(&content).ok())
        .unwrap_or_else(IntegrationConfig::generated)
}

pub fn save(path: &Path, config: &IntegrationConfig) -> Result<(), BridgeError> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let temporary = path.with_extension("json.tmp");
    fs::write(&temporary, serde_json::to_vec_pretty(config)?)?;
    fs::rename(&temporary, path)?;
    Ok(())
}

pub fn generate_token() -> String {
    let mut bytes = [0u8; TOKEN_BYTES];
    OsRng.fill_bytes(&mut bytes);
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    #[test]
    fn missing_file_gives_disabled_default_with_token() {
        let folder = tempfile::tempdir().unwrap();
        let config = load(&folder.path().join(CONFIG_FILE_NAME));
        assert!(!config.enabled);
        assert_eq!(config.port, DEFAULT_PORT);
        assert_eq!(config.token.len(), TOKEN_BYTES * 2);
    }

    #[test]
    fn round_trip() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join("Réglages").join(CONFIG_FILE_NAME);
        let config = IntegrationConfig {
            enabled: true,
            port: 52000,
            token: "abc".to_owned(),
        };
        save(&path, &config).unwrap();
        assert_eq!(load(&path), config);
    }

    #[test]
    fn tokens_are_random() {
        assert_ne!(generate_token(), generate_token());
    }
}
