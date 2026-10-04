use serde::Deserialize;
use tauri::{ipc::Channel, AppHandle, State};
use tauri_plugin_opener::OpenerExt;

use crate::access::AccessLock;
use crate::error::BridgeError;
use crate::paths::settings_file;
use crate::runs::RunId;
use crate::sidecar::{path_argument, start_streaming_run, EngineMessage, EngineRuns};

/// Only the official download pages of the tools Drawflow relies on can be opened.
const DOWNLOAD_PAGES: [&str; 4] = [
    "https://www.opendesign.com/",
    "https://ollama.com/",
    "https://www.elgato.com/",
    "https://github.com/pepito2t/drawflow-engine/releases/",
];

/// Allow-listed installation fixes run by the engine.
#[derive(Clone, Copy, Debug, PartialEq, Deserialize)]
pub enum SetupAction {
    #[serde(rename = "oda.install")]
    OdaInstall,
    #[serde(rename = "oda.use-detected")]
    OdaUseDetected,
    #[serde(rename = "ollama.install")]
    OllamaInstall,
    #[serde(rename = "ollama.start")]
    OllamaStart,
    #[serde(rename = "model.pull")]
    ModelPull,
}

impl SetupAction {
    fn id(self) -> &'static str {
        match self {
            Self::OdaInstall => "oda.install",
            Self::OdaUseDetected => "oda.use-detected",
            Self::OllamaInstall => "ollama.install",
            Self::OllamaStart => "ollama.start",
            Self::ModelPull => "model.pull",
        }
    }
}

#[tauri::command]
pub fn run_setup_action(
    app: AppHandle,
    runs: State<'_, EngineRuns>,
    lock: State<'_, AccessLock>,
    action: SetupAction,
    on_event: Channel<EngineMessage>,
) -> Result<RunId, BridgeError> {
    lock.ensure_unlocked()?;
    let settings = path_argument(settings_file(&app)?);
    let run_key = format!("setup:{}", action.id());
    start_streaming_run(
        app,
        &runs,
        &run_key,
        setup_arguments(action, settings),
        on_event,
        None,
    )
}

#[tauri::command]
pub fn open_download_page(
    app: AppHandle,
    lock: State<'_, AccessLock>,
    url: String,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    if !is_download_page(&url) {
        return Err(BridgeError::PageNotAllowed);
    }
    app.opener().open_url(url, None::<&str>)?;
    Ok(())
}

fn is_download_page(url: &str) -> bool {
    DOWNLOAD_PAGES.iter().any(|page| url.starts_with(page))
}

fn setup_arguments(action: SetupAction, settings: String) -> Vec<String> {
    vec![
        "setup".to_owned(),
        "run".to_owned(),
        action.id().to_owned(),
        "--settings".to_owned(),
        settings,
    ]
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    #[test]
    fn actions_are_allow_listed_by_name() {
        let action: SetupAction = serde_json::from_str("\"model.pull\"").unwrap();
        assert_eq!(
            setup_arguments(action, "s é.json".to_owned()),
            ["setup", "run", "model.pull", "--settings", "s é.json"]
        );
        assert!(serde_json::from_str::<SetupAction>("\"winget\"").is_err());
    }

    #[test]
    fn only_official_download_pages_can_be_opened() {
        assert!(is_download_page("https://ollama.com/download"));
        assert!(is_download_page(
            "https://github.com/pepito2t/drawflow-engine/releases/download/v0.3.0/ch.drawflow.streamDeckPlugin"
        ));
        assert!(!is_download_page("https://ollama.com.evil.example/"));
        assert!(!is_download_page("file:///C:/Windows/System32/calc.exe"));
        assert!(!is_download_page(
            "https://github.com/someone-else/releases/"
        ));
    }
}
