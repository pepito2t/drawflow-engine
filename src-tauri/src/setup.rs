use serde::Deserialize;
use tauri::{ipc::Channel, AppHandle, State};
use tauri_plugin_opener::OpenerExt;

use crate::access::AccessLock;
use crate::error::BridgeError;
use crate::paths::settings_file;
use crate::runs::RunId;
use crate::sidecar::{path_argument, start_streaming_run, EngineMessage, EngineRuns};

/// Only the official download pages of the tools Drawflow relies on can be opened.
/// Every prefix ends with `/` so a sibling path (`…_evil/`) cannot match.
const DOWNLOAD_PAGES: [&str; 5] = [
    "https://www.opendesign.com/",
    "https://ollama.com/",
    "https://mirabox.net/",
    "https://github.com/pepito2t/drawflow-engine/releases/",
    "https://github.com/pepito2t/streamdock_autocad/",
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
    #[serde(rename = "streamdock.install-plugin")]
    StreamDockInstallPlugin,
    #[serde(rename = "streamdock.install-autocad-plugin")]
    StreamDockInstallAutocadPlugin,
}

impl SetupAction {
    fn id(self) -> &'static str {
        match self {
            Self::OdaInstall => "oda.install",
            Self::OdaUseDetected => "oda.use-detected",
            Self::OllamaInstall => "ollama.install",
            Self::OllamaStart => "ollama.start",
            Self::ModelPull => "model.pull",
            Self::StreamDockInstallPlugin => "streamdock.install-plugin",
            Self::StreamDockInstallAutocadPlugin => "streamdock.install-autocad-plugin",
        }
    }
}

#[tauri::command]
pub async fn run_setup_action(
    app: AppHandle,
    runs: State<'_, EngineRuns>,
    lock: State<'_, AccessLock>,
    action: SetupAction,
    on_event: Channel<EngineMessage>,
) -> Result<RunId, BridgeError> {
    lock.ensure_unlocked()?;
    if action == SetupAction::StreamDockInstallPlugin {
        crate::integrations::ensure_enabled(&app).await?;
    }
    let settings = path_argument(settings_file(&app)?);
    let version = app.package_info().version.to_string();
    let run_key = format!("setup:{}", action.id());
    let arguments = setup_arguments(action, settings, version);
    start_streaming_run(app, &runs, &run_key, arguments, on_event, None)
}

/// Downloads a model through Ollama; the engine validates the name, Rust only keeps it from
/// being read as a command-line option.
#[tauri::command]
pub fn pull_model(
    app: AppHandle,
    runs: State<'_, EngineRuns>,
    lock: State<'_, AccessLock>,
    model: String,
    on_event: Channel<EngineMessage>,
) -> Result<RunId, BridgeError> {
    lock.ensure_unlocked()?;
    if !is_model_name(&model) {
        return Err(BridgeError::InvalidModelName(model));
    }
    let settings = path_argument(settings_file(&app)?);
    let run_key = format!("model:{model}");
    start_streaming_run(
        app,
        &runs,
        &run_key,
        pull_arguments(&model, settings),
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

fn is_model_name(model: &str) -> bool {
    !model.starts_with('-')
        && !model.is_empty()
        && model
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '.' | '_' | '-' | ':' | '/'))
}

fn pull_arguments(model: &str, settings: String) -> Vec<String> {
    vec![
        "assistant".to_owned(),
        "pull".to_owned(),
        model.to_owned(),
        "--settings".to_owned(),
        settings,
    ]
}

fn setup_arguments(action: SetupAction, settings: String, app_version: String) -> Vec<String> {
    vec![
        "setup".to_owned(),
        "run".to_owned(),
        action.id().to_owned(),
        "--settings".to_owned(),
        settings,
        "--app-version".to_owned(),
        app_version,
    ]
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    #[test]
    fn actions_are_allow_listed_by_name() {
        let action: SetupAction = serde_json::from_str("\"streamdock.install-plugin\"").unwrap();
        assert_eq!(
            setup_arguments(action, "s é.json".to_owned(), "0.7.0".to_owned()),
            [
                "setup",
                "run",
                "streamdock.install-plugin",
                "--settings",
                "s é.json",
                "--app-version",
                "0.7.0"
            ]
        );
        assert!(serde_json::from_str::<SetupAction>("\"winget\"").is_err());
    }

    #[test]
    fn model_names_cannot_become_options() {
        assert!(is_model_name("qwen3.5:9b"));
        assert!(is_model_name("library/llama3.1:8b"));
        assert!(!is_model_name("--settings"));
        assert!(!is_model_name("qwen 3"));
        assert!(!is_model_name(""));
        assert_eq!(
            pull_arguments("qwen3.5:4b", "s.json".to_owned()),
            ["assistant", "pull", "qwen3.5:4b", "--settings", "s.json"]
        );
    }

    #[test]
    fn only_official_download_pages_can_be_opened() {
        assert!(is_download_page("https://ollama.com/download"));
        assert!(is_download_page(
            "https://github.com/pepito2t/drawflow-engine/releases/download/v0.3.0/ch.drawflow.streamDeckPlugin"
        ));
        assert!(is_download_page(
            "https://github.com/pepito2t/streamdock_autocad/releases/latest"
        ));
        assert!(!is_download_page("https://ollama.com.evil.example/"));
        assert!(!is_download_page("file:///C:/Windows/System32/calc.exe"));
        assert!(!is_download_page(
            "https://github.com/someone-else/releases/"
        ));
        assert!(!is_download_page(
            "https://github.com/pepito2t/streamdock_autocad_evil/releases/latest"
        ));
    }

    #[test]
    fn every_download_page_prefix_ends_with_a_slash() {
        assert!(DOWNLOAD_PAGES.iter().all(|page| page.ends_with('/')));
    }
}
