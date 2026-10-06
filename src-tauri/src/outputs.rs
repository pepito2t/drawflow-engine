use std::collections::HashSet;
use std::path::Path;
use std::sync::Mutex;

use serde::Deserialize;
use tauri::{AppHandle, State};
use tauri_plugin_opener::OpenerExt;

use crate::access::AccessLock;
use crate::error::BridgeError;
use crate::paths::settings_file;

const LOGS_FOLDER: &str = "logs";

/// Files the engine reported in its `result` events: the only ones the UI may open.
#[derive(Default)]
pub struct KnownOutputs(Mutex<HashSet<String>>);

#[derive(Deserialize)]
struct ResultLine {
    #[serde(rename = "type")]
    kind: String,
    #[serde(default)]
    outputs: Vec<String>,
}

impl KnownOutputs {
    pub fn remember_from_line(&self, line: &str) {
        if !line.contains("\"result\"") {
            return;
        }
        let Ok(event) = serde_json::from_str::<ResultLine>(line) else {
            return;
        };
        if event.kind != "result" {
            return;
        }
        if let Ok(mut known) = self.0.lock() {
            known.extend(event.outputs);
        }
    }

    fn contains(&self, path: &str) -> Result<bool, BridgeError> {
        let known = self.0.lock().map_err(|_| BridgeError::StatePoisoned)?;
        Ok(known.contains(path))
    }
}

/// Opens the engine's diagnostic log folder in the file manager (created if needed).
#[tauri::command]
pub fn open_logs_folder(app: AppHandle, lock: State<'_, AccessLock>) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    let folder = settings_file(&app)?
        .parent()
        .map(|parent| parent.join(LOGS_FOLDER))
        .ok_or(BridgeError::StatePoisoned)?;
    std::fs::create_dir_all(&folder)?;
    app.opener()
        .open_path(folder.to_string_lossy(), None::<&str>)?;
    Ok(())
}

/// Opens a file produced by a run with the system's default application.
#[tauri::command]
pub fn open_output(
    app: AppHandle,
    lock: State<'_, AccessLock>,
    outputs: State<'_, KnownOutputs>,
    path: String,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    if !outputs.contains(&path)? {
        return Err(BridgeError::OutputNotAllowed(path));
    }
    if !Path::new(&path).is_file() {
        return Err(BridgeError::OutputMissing(path));
    }
    app.opener().open_path(path, None::<&str>)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    #[test]
    fn only_outputs_of_result_events_become_known() {
        let outputs = KnownOutputs::default();
        outputs.remember_from_line(r#"{"type":"log","message":"result"}"#);
        outputs.remember_from_line("not json \"result\"");
        outputs.remember_from_line(
            r#"{"type":"result","summary":"ok","outputs":["C:\\Sortie\\liste é.xlsx"]}"#,
        );

        assert!(outputs.contains("C:\\Sortie\\liste é.xlsx").unwrap());
        assert!(!outputs.contains("C:\\Windows\\System32\\calc.exe").unwrap());
    }
}
