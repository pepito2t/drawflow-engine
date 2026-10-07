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
/// Documents handed to their default application; anything else is only revealed in its folder.
const OPENABLE_EXTENSIONS: [&str; 13] = [
    "pdf", "docx", "xlsx", "xlsm", "csv", "txt", "dwg", "dxf", "png", "jpg", "jpeg", "md", "json",
];

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

#[derive(Deserialize)]
struct MailDetail {
    #[serde(default)]
    messages: Vec<MailMessage>,
}

#[derive(Deserialize)]
struct MailMessage {
    #[serde(default)]
    attachments: Vec<MailAttachment>,
}

#[derive(Deserialize)]
struct MailAttachment {
    #[serde(default)]
    file: Option<String>,
}

#[derive(Deserialize)]
struct HistoryListing {
    entries: Vec<HistoryOutputs>,
}

#[derive(Deserialize)]
struct HistoryOutputs {
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

    /// Past runs listed from the history may be reopened too.
    pub fn remember_from_history(&self, json: &str) {
        let Ok(listing) = serde_json::from_str::<HistoryListing>(json) else {
            return;
        };
        if let Ok(mut known) = self.0.lock() {
            known.extend(listing.entries.into_iter().flat_map(|entry| entry.outputs));
        }
    }

    /// Attachments of a conversation shown in the Mail tab may be opened too.
    pub fn remember_from_mail(&self, json: &str) {
        let Ok(detail) = serde_json::from_str::<MailDetail>(json) else {
            return;
        };
        if let Ok(mut known) = self.0.lock() {
            known.extend(
                detail
                    .messages
                    .into_iter()
                    .flat_map(|message| message.attachments)
                    .filter_map(|attachment| attachment.file),
            );
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
    std::fs::create_dir_all(&folder).map_err(BridgeError::LogsFolder)?;
    app.opener()
        .open_path(folder.to_string_lossy(), None::<&str>)?;
    Ok(())
}

/// Opens a document produced by a run with its default application, or reveals any other
/// produced file in its folder so nothing executable is ever launched.
#[tauri::command(async)]
pub async fn open_output(
    app: AppHandle,
    lock: State<'_, AccessLock>,
    outputs: State<'_, KnownOutputs>,
    path: String,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    if !outputs.contains(&path)? {
        return Err(BridgeError::OutputNotAllowed(path));
    }
    let checked = path.clone();
    let exists =
        tauri::async_runtime::spawn_blocking(move || Path::new(&checked).is_file()).await?;
    if !exists {
        return Err(BridgeError::OutputMissing(path));
    }
    if opens_directly(&path) {
        app.opener().open_path(path, None::<&str>)?;
    } else {
        app.opener().reveal_item_in_dir(path)?;
    }
    Ok(())
}

pub fn opens_directly(path: &str) -> bool {
    Path::new(path)
        .extension()
        .and_then(|extension| extension.to_str())
        .map(|extension| OPENABLE_EXTENSIONS.contains(&extension.to_ascii_lowercase().as_str()))
        .unwrap_or(false)
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

    #[test]
    fn history_listings_make_past_outputs_known() {
        let outputs = KnownOutputs::default();
        outputs.remember_from_history(
            r#"{"entries":[{"id":"a","outputs":["C:\\Sortie\\ancien.xlsx"]},{"id":"b"}]}"#,
        );
        outputs.remember_from_history("pas du json");

        assert!(outputs.contains("C:\\Sortie\\ancien.xlsx").unwrap());
    }

    #[test]
    fn documents_open_directly_whatever_the_case_of_the_extension() {
        assert!(opens_directly("C:\\Sortie\\liste é.XLSX"));
        assert!(opens_directly("C:\\Sortie\\rapport.docx"));
        assert!(opens_directly("C:\\Sortie\\plan.dwg"));
        assert!(opens_directly("/tmp/export.Json"));
    }

    #[test]
    fn executables_and_unknown_files_are_only_revealed() {
        assert!(!opens_directly("C:\\Sortie\\installer.exe"));
        assert!(!opens_directly("C:\\Sortie\\script.bat"));
        assert!(!opens_directly("C:\\Sortie\\liste.xlsx.lnk"));
        assert!(!opens_directly("C:\\Sortie\\archive.zip"));
        assert!(!opens_directly("C:\\Sortie\\sans-extension"));
    }
}
