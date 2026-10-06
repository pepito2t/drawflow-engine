use std::io::Write;
use std::path::PathBuf;

use serde::{Deserialize, Serialize};
use tauri::{ipc::Channel, AppHandle, Manager, State};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;
use tempfile::NamedTempFile;

use crate::access::AccessLock;
use crate::error::BridgeError;
use crate::outputs::KnownOutputs;
use crate::paths::settings_file;
use crate::runs::{Killable, RunId, RunRegistry};

pub(crate) const SIDECAR_NAME: &str = "engine";
const INPUT_FILE_PREFIX: &str = "drawflow-input-";
const INPUT_FILE_SUFFIX: &str = ".json";

pub type EngineRuns = RunRegistry<CommandChild>;

impl Killable for CommandChild {
    fn kill_process(self) -> Result<(), BridgeError> {
        Ok(self.kill()?)
    }
}

/// Raw transport messages; the UI owns the interpretation of engine events.
#[derive(Clone, Debug, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "lowercase")]
pub enum EngineMessage {
    Stdout { line: String },
    Stderr { line: String },
    Exit { code: Option<i32> },
}

/// Output of a one-shot engine command; on failure stdout carries an NDJSON error event.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct EngineOutput {
    success: bool,
    stdout: String,
}

#[tauri::command]
pub async fn list_modules(
    app: AppHandle,
    lock: State<'_, AccessLock>,
) -> Result<EngineOutput, BridgeError> {
    lock.ensure_unlocked()?;
    query_engine(&app, vec!["list-modules".to_owned()]).await
}

#[tauri::command]
pub async fn get_settings(
    app: AppHandle,
    lock: State<'_, AccessLock>,
) -> Result<EngineOutput, BridgeError> {
    lock.ensure_unlocked()?;
    let settings = path_argument(settings_file(&app)?);
    query_engine(&app, settings_arguments("get", settings, None)).await
}

#[tauri::command]
pub async fn save_settings(
    app: AppHandle,
    lock: State<'_, AccessLock>,
    values: serde_json::Value,
) -> Result<EngineOutput, BridgeError> {
    lock.ensure_unlocked()?;
    let settings = path_argument(settings_file(&app)?);
    let input_file = write_input_file(&values)?;
    let input = path_argument(input_file.path().to_path_buf());
    let output = query_engine(&app, settings_arguments("set", settings, Some(input))).await;
    drop(input_file);
    output
}

/// Allow-listed file-based engine requests (templates, settings import/export).
#[derive(Clone, Copy, Debug, PartialEq, Deserialize)]
pub enum EngineRequest {
    #[serde(rename = "templates.list")]
    TemplatesList,
    #[serde(rename = "templates.import")]
    TemplatesImport,
    #[serde(rename = "templates.remove")]
    TemplatesRemove,
    #[serde(rename = "templates.set-default")]
    TemplatesSetDefault,
    #[serde(rename = "presets.list")]
    PresetsList,
    #[serde(rename = "presets.save")]
    PresetsSave,
    #[serde(rename = "presets.remove")]
    PresetsRemove,
    #[serde(rename = "settings.export")]
    SettingsExport,
    #[serde(rename = "settings.read-import")]
    SettingsReadImport,
    #[serde(rename = "assistant.models")]
    AssistantModels,
    #[serde(rename = "assistant.history-get")]
    AssistantHistoryGet,
    #[serde(rename = "assistant.history-save")]
    AssistantHistorySave,
    #[serde(rename = "assistant.catalog")]
    AssistantCatalog,
    #[serde(rename = "assistant.model-delete")]
    AssistantModelDelete,
    #[serde(rename = "help.guide")]
    HelpGuide,
    #[serde(rename = "setup.scan")]
    SetupScan,
    #[serde(rename = "settings.add-synonyms")]
    SettingsAddSynonyms,
    #[serde(rename = "history.list")]
    HistoryList,
    #[serde(rename = "history.remove")]
    HistoryRemove,
    #[serde(rename = "history.clear")]
    HistoryClear,
}

impl EngineRequest {
    fn command(self) -> (&'static str, &'static str) {
        match self {
            Self::TemplatesList => ("templates", "list"),
            Self::TemplatesImport => ("templates", "import"),
            Self::TemplatesRemove => ("templates", "remove"),
            Self::TemplatesSetDefault => ("templates", "set-default"),
            Self::PresetsList => ("presets", "list"),
            Self::PresetsSave => ("presets", "save"),
            Self::PresetsRemove => ("presets", "remove"),
            Self::SettingsExport => ("settings", "export"),
            Self::SettingsReadImport => ("settings", "read-import"),
            Self::AssistantModels => ("assistant", "models"),
            Self::AssistantHistoryGet => ("assistant", "history-get"),
            Self::AssistantHistorySave => ("assistant", "history-save"),
            Self::AssistantCatalog => ("assistant", "catalog"),
            Self::AssistantModelDelete => ("assistant", "model-delete"),
            Self::HelpGuide => ("help", "guide"),
            Self::SetupScan => ("setup", "scan"),
            Self::SettingsAddSynonyms => ("settings", "add-synonyms"),
            Self::HistoryList => ("history", "list"),
            Self::HistoryRemove => ("history", "remove"),
            Self::HistoryClear => ("history", "clear"),
        }
    }
}

#[tauri::command]
pub async fn engine_request(
    app: AppHandle,
    lock: State<'_, AccessLock>,
    request: EngineRequest,
    payload: serde_json::Value,
) -> Result<EngineOutput, BridgeError> {
    lock.ensure_unlocked()?;
    let settings = path_argument(settings_file(&app)?);
    let input_file = write_input_file(&payload)?;
    let input = path_argument(input_file.path().to_path_buf());
    let version = app.package_info().version.to_string();
    let arguments = request_arguments(request, settings, input, version);
    let output = query_engine(&app, arguments).await;
    drop(input_file);
    if request == EngineRequest::HistoryList {
        if let Ok(listed) = &output {
            app.state::<KnownOutputs>()
                .remember_from_history(&listed.stdout);
        }
    }
    output
}

#[tauri::command]
pub fn run_module(
    app: AppHandle,
    runs: State<'_, EngineRuns>,
    lock: State<'_, AccessLock>,
    module_id: String,
    inputs: serde_json::Value,
    on_event: Channel<EngineMessage>,
) -> Result<RunId, BridgeError> {
    lock.ensure_unlocked()?;
    if !is_module_id(&module_id) {
        return Err(BridgeError::InvalidModuleId(module_id));
    }
    let input_file = write_input_file(&inputs)?;
    let input_path = path_argument(input_file.path().to_path_buf());
    let settings_path = path_argument(settings_file(&app)?);
    let arguments = run_arguments(&module_id, input_path, settings_path);
    start_streaming_run(
        app,
        &runs,
        &module_id,
        arguments,
        on_event,
        Some(input_file),
    )
}

/// Spawns a long engine command tracked by the run registry, relaying its output to the UI.
pub(crate) fn start_streaming_run(
    app: AppHandle,
    runs: &EngineRuns,
    run_key: &str,
    arguments: Vec<String>,
    on_event: Channel<EngineMessage>,
    input_file: Option<NamedTempFile>,
) -> Result<RunId, BridgeError> {
    let (run_id, mut receiver) = runs.start(run_key, || {
        Ok(app.shell().sidecar(SIDECAR_NAME)?.args(arguments).spawn()?)
    })?;
    let task_run_id = run_id.clone();
    tauri::async_runtime::spawn(async move {
        let outputs = app.state::<KnownOutputs>();
        let remember = |line: &str| outputs.remember_from_line(line);
        if let Err(error) = relay_events(&mut receiver, &on_event, remember).await {
            eprintln!("Relais des événements interrompu ({task_run_id}) : {error}");
        }
        let runs = app.state::<EngineRuns>();
        if let Err(error) = runs.finish(&task_run_id) {
            eprintln!("Fin de traitement non enregistrée ({task_run_id}) : {error}");
        }
        drop(input_file);
    });
    Ok(run_id)
}

#[tauri::command]
pub fn cancel_run(runs: State<'_, EngineRuns>, run_id: RunId) -> Result<(), BridgeError> {
    runs.cancel(&run_id)
}

async fn query_engine(
    app: &AppHandle,
    arguments: Vec<String>,
) -> Result<EngineOutput, BridgeError> {
    let output = app
        .shell()
        .sidecar(SIDECAR_NAME)?
        .args(arguments)
        .output()
        .await?;
    Ok(EngineOutput {
        success: output.status.success(),
        stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
    })
}

/// Module ids come from `list-modules`; anything else must not reach the engine's CLI parser.
fn is_module_id(module_id: &str) -> bool {
    !module_id.is_empty()
        && !module_id.starts_with('-')
        && module_id
            .chars()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || matches!(c, '-' | '_'))
}

fn run_arguments(module_id: &str, input: String, settings: String) -> Vec<String> {
    vec![
        "run".to_owned(),
        module_id.to_owned(),
        "--input".to_owned(),
        input,
        "--settings".to_owned(),
        settings,
    ]
}

fn settings_arguments(action: &str, settings: String, input: Option<String>) -> Vec<String> {
    let mut arguments = vec![
        "settings".to_owned(),
        action.to_owned(),
        "--settings".to_owned(),
        settings,
    ];
    if let Some(input) = input {
        arguments.extend(["--input".to_owned(), input]);
    }
    arguments
}

fn request_arguments(
    request: EngineRequest,
    settings: String,
    input: String,
    app_version: String,
) -> Vec<String> {
    let (group, action) = request.command();
    vec![
        group.to_owned(),
        action.to_owned(),
        "--settings".to_owned(),
        settings,
        "--input".to_owned(),
        input,
        "--app-version".to_owned(),
        app_version,
    ]
}

pub(crate) fn path_argument(path: PathBuf) -> String {
    path.to_string_lossy().into_owned()
}

pub(crate) async fn relay_events(
    receiver: &mut tauri::async_runtime::Receiver<CommandEvent>,
    channel: &Channel<EngineMessage>,
    on_stdout: impl Fn(&str),
) -> Result<(), BridgeError> {
    while let Some(event) = receiver.recv().await {
        let is_terminal = matches!(event, CommandEvent::Terminated(_));
        if let Some(message) = to_message(event) {
            if let EngineMessage::Stdout { line } = &message {
                on_stdout(line);
            }
            channel.send(message)?;
        }
        if is_terminal {
            break;
        }
    }
    Ok(())
}

fn to_message(event: CommandEvent) -> Option<EngineMessage> {
    match event {
        CommandEvent::Stdout(bytes) => Some(EngineMessage::Stdout {
            line: decode_line(&bytes),
        }),
        CommandEvent::Stderr(bytes) => Some(EngineMessage::Stderr {
            line: decode_line(&bytes),
        }),
        CommandEvent::Error(line) => Some(EngineMessage::Stderr { line }),
        CommandEvent::Terminated(payload) => Some(EngineMessage::Exit { code: payload.code }),
        _ => None,
    }
}

fn decode_line(bytes: &[u8]) -> String {
    String::from_utf8_lossy(bytes)
        .trim_end_matches(['\r', '\n'])
        .to_owned()
}

pub(crate) fn write_input_file(inputs: &serde_json::Value) -> Result<NamedTempFile, BridgeError> {
    let mut file = tempfile::Builder::new()
        .prefix(INPUT_FILE_PREFIX)
        .suffix(INPUT_FILE_SUFFIX)
        .tempfile()?;
    serde_json::to_writer(&mut file, inputs)?;
    file.flush()?;
    Ok(file)
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;
    use tauri_plugin_shell::process::TerminatedPayload;

    #[test]
    fn module_ids_cannot_become_options() {
        assert!(is_module_id("dwg-parts"));
        assert!(is_module_id("pdf_report2"));
        assert!(!is_module_id("--settings"));
        assert!(!is_module_id(""));
        assert!(!is_module_id("Dwg Parts"));
    }

    #[test]
    fn decode_line_strips_windows_and_unix_line_endings() {
        assert_eq!(decode_line(b"{\"type\":\"log\"}\r\n"), "{\"type\":\"log\"}");
        assert_eq!(decode_line("é\n".as_bytes()), "é");
    }

    #[test]
    fn stdout_is_relayed_without_interpretation() {
        let message = to_message(CommandEvent::Stdout(b"not json\n".to_vec()));
        assert_eq!(
            message,
            Some(EngineMessage::Stdout {
                line: "not json".to_owned()
            })
        );
    }

    #[test]
    fn termination_becomes_exit_message() {
        let payload = TerminatedPayload {
            code: Some(2),
            signal: None,
        };
        assert_eq!(
            to_message(CommandEvent::Terminated(payload)),
            Some(EngineMessage::Exit { code: Some(2) })
        );
    }

    #[test]
    fn run_arguments_pass_input_and_settings_files() {
        let arguments = run_arguments(
            "hello",
            "in é.json".to_owned(),
            "C:\\cfg\\settings.json".to_owned(),
        );
        assert_eq!(
            arguments,
            [
                "run",
                "hello",
                "--input",
                "in é.json",
                "--settings",
                "C:\\cfg\\settings.json"
            ]
        );
    }

    #[test]
    fn settings_arguments_add_input_only_when_saving() {
        assert_eq!(
            settings_arguments("get", "s.json".to_owned(), None),
            ["settings", "get", "--settings", "s.json"]
        );
        assert_eq!(
            settings_arguments("set", "s.json".to_owned(), Some("v.json".to_owned())),
            [
                "settings",
                "set",
                "--settings",
                "s.json",
                "--input",
                "v.json"
            ]
        );
    }

    #[test]
    fn requests_are_allow_listed_by_name() {
        let request: EngineRequest = serde_json::from_str("\"templates.import\"").unwrap();
        assert_eq!(
            request_arguments(
                request,
                "s.json".to_owned(),
                "r.json".to_owned(),
                "0.8.1".to_owned()
            ),
            [
                "templates",
                "import",
                "--settings",
                "s.json",
                "--input",
                "r.json",
                "--app-version",
                "0.8.1"
            ]
        );
        assert!(serde_json::from_str::<EngineRequest>("\"run\"").is_err());
    }

    #[test]
    fn exit_message_serializes_with_kind_tag() {
        let json = serde_json::to_string(&EngineMessage::Exit { code: None }).unwrap();
        assert_eq!(json, r#"{"kind":"exit","code":null}"#);
    }

    #[test]
    fn input_file_contains_inputs_as_json() {
        let inputs = serde_json::json!({ "name": "Zoé", "output_folder": "C:\\Sortie é" });
        let file = write_input_file(&inputs).unwrap();
        let written: serde_json::Value =
            serde_json::from_str(&std::fs::read_to_string(file.path()).unwrap()).unwrap();
        assert_eq!(written, inputs);
    }
}
