use std::path::PathBuf;

use tauri::{AppHandle, Manager};

use crate::error::BridgeError;

const SETTINGS_FILE_NAME: &str = "settings.json";

pub fn settings_file(app: &AppHandle) -> Result<PathBuf, BridgeError> {
    Ok(app.path().app_config_dir()?.join(SETTINGS_FILE_NAME))
}
