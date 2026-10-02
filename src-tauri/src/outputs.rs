use std::path::Path;

use tauri::{AppHandle, State};
use tauri_plugin_opener::OpenerExt;

use crate::access::AccessLock;
use crate::error::BridgeError;

/// Opens a file produced by a run with the system's default application.
#[tauri::command]
pub fn open_output(
    app: AppHandle,
    lock: State<'_, AccessLock>,
    path: String,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    if !Path::new(&path).is_file() {
        return Err(BridgeError::OutputMissing(path));
    }
    app.opener().open_path(path, None::<&str>)?;
    Ok(())
}
