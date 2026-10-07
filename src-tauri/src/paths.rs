use std::fs;
use std::path::{Path, PathBuf};

use tauri::{AppHandle, Manager};

use crate::error::BridgeError;

const SETTINGS_FILE_NAME: &str = "settings.json";

pub fn settings_file(app: &AppHandle) -> Result<PathBuf, BridgeError> {
    Ok(app.path().app_config_dir()?.join(SETTINGS_FILE_NAME))
}

/// Writes next to the target then renames, so a crash never leaves a half-written file.
pub fn write_atomically(path: &Path, content: &[u8]) -> std::io::Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let temporary = path.with_extension("json.tmp");
    fs::write(&temporary, content)?;
    fs::rename(&temporary, path)
}
