use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Manager};

use crate::error::BridgeError;
use crate::paths::write_atomically;

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
    pub fn generated() -> Result<Self, BridgeError> {
        Ok(Self {
            enabled: false,
            port: DEFAULT_PORT,
            token: generate_token()?,
        })
    }
}

pub fn config_file(app: &AppHandle) -> Result<PathBuf, BridgeError> {
    Ok(app.path().app_config_dir()?.join(CONFIG_FILE_NAME))
}

/// A missing file yields a disabled default with a fresh token; a corrupt one is an error,
/// never silently replaced.
pub fn load(path: &Path) -> Result<IntegrationConfig, BridgeError> {
    let content = match fs::read_to_string(path) {
        Ok(content) => content,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return IntegrationConfig::generated()
        }
        Err(error) => return Err(BridgeError::IntegrationsFile(error)),
    };
    serde_json::from_str(&content)
        .map_err(|_| BridgeError::ConfigCorrupted(CONFIG_FILE_NAME.to_owned()))
}

pub fn save(path: &Path, config: &IntegrationConfig) -> Result<(), BridgeError> {
    let content = serde_json::to_vec_pretty(config)?;
    write_atomically(path, &content).map_err(BridgeError::IntegrationsFile)
}

pub fn generate_token() -> Result<String, BridgeError> {
    let mut bytes = [0u8; TOKEN_BYTES];
    getrandom::fill(&mut bytes).map_err(BridgeError::TokenGeneration)?;
    Ok(bytes.iter().map(|byte| format!("{byte:02x}")).collect())
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    #[test]
    fn missing_file_gives_disabled_default_with_token() {
        let folder = tempfile::tempdir().unwrap();
        let config = load(&folder.path().join(CONFIG_FILE_NAME)).unwrap();
        assert!(!config.enabled);
        assert_eq!(config.port, DEFAULT_PORT);
        assert_eq!(config.token.len(), TOKEN_BYTES * 2);
    }

    #[test]
    fn corrupt_file_is_an_error_not_a_fresh_token() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join(CONFIG_FILE_NAME);
        fs::write(&path, "{ pas du json").unwrap();
        assert!(matches!(load(&path), Err(BridgeError::ConfigCorrupted(_))));
        assert_eq!(fs::read_to_string(&path).unwrap(), "{ pas du json");
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
        assert_eq!(load(&path).unwrap(), config);
    }

    #[test]
    fn tokens_are_random() {
        assert_ne!(generate_token().unwrap(), generate_token().unwrap());
    }
}
