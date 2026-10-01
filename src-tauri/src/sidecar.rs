use std::io::Write;
use std::path::PathBuf;
use std::sync::{Mutex, MutexGuard};

use serde::Serialize;
use tauri::{ipc::Channel, AppHandle, State};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;
use tempfile::NamedTempFile;

use crate::error::BridgeError;
use crate::paths::settings_file;

const SIDECAR_NAME: &str = "engine";
const INPUT_FILE_PREFIX: &str = "drawflow-input-";
const INPUT_FILE_SUFFIX: &str = ".json";

#[derive(Default)]
pub struct RunningEngine(Mutex<Option<CommandChild>>);

impl RunningEngine {
    fn lock(&self) -> Result<MutexGuard<'_, Option<CommandChild>>, BridgeError> {
        self.0.lock().map_err(|_| BridgeError::StatePoisoned)
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
pub async fn list_modules(app: AppHandle) -> Result<EngineOutput, BridgeError> {
    query_engine(&app, vec!["list-modules".to_owned()]).await
}

#[tauri::command]
pub async fn get_settings(app: AppHandle) -> Result<EngineOutput, BridgeError> {
    let settings = path_argument(settings_file(&app)?);
    query_engine(&app, settings_arguments("get", settings, None)).await
}

#[tauri::command]
pub async fn save_settings(
    app: AppHandle,
    values: serde_json::Value,
) -> Result<EngineOutput, BridgeError> {
    let settings = path_argument(settings_file(&app)?);
    let input_file = write_input_file(&values)?;
    let input = path_argument(input_file.path().to_path_buf());
    let output = query_engine(&app, settings_arguments("set", settings, Some(input))).await;
    drop(input_file);
    output
}

#[tauri::command]
pub async fn run_module(
    app: AppHandle,
    engine: State<'_, RunningEngine>,
    module_id: String,
    inputs: serde_json::Value,
    on_event: Channel<EngineMessage>,
) -> Result<(), BridgeError> {
    let input_file = write_input_file(&inputs)?;
    let input_path = path_argument(input_file.path().to_path_buf());
    let settings_path = path_argument(settings_file(&app)?);
    let mut receiver = {
        let mut running = engine.lock()?;
        if running.is_some() {
            return Err(BridgeError::RunInProgress);
        }
        let (receiver, child) = app
            .shell()
            .sidecar(SIDECAR_NAME)?
            .args(run_arguments(&module_id, input_path, settings_path))
            .spawn()?;
        *running = Some(child);
        receiver
    };

    let relay_result = relay_events(&mut receiver, &on_event).await;
    engine.lock()?.take();
    drop(input_file);
    relay_result
}

#[tauri::command]
pub fn cancel_run(engine: State<'_, RunningEngine>) -> Result<(), BridgeError> {
    if let Some(child) = engine.lock()?.take() {
        child.kill()?;
    }
    Ok(())
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

fn path_argument(path: PathBuf) -> String {
    path.to_string_lossy().into_owned()
}

async fn relay_events(
    receiver: &mut tauri::async_runtime::Receiver<CommandEvent>,
    channel: &Channel<EngineMessage>,
) -> Result<(), BridgeError> {
    while let Some(event) = receiver.recv().await {
        let is_terminal = matches!(event, CommandEvent::Terminated(_));
        if let Some(message) = to_message(event) {
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

fn write_input_file(inputs: &serde_json::Value) -> Result<NamedTempFile, BridgeError> {
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
