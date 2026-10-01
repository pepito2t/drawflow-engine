use std::io::Write;
use std::sync::{Mutex, MutexGuard};

use serde::Serialize;
use tauri::{ipc::Channel, AppHandle, State};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;
use tempfile::NamedTempFile;

use crate::error::BridgeError;

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

#[tauri::command]
pub async fn list_modules(app: AppHandle) -> Result<String, BridgeError> {
    let output = app
        .shell()
        .sidecar(SIDECAR_NAME)?
        .args(["list-modules"])
        .output()
        .await?;
    let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
    if output.status.success() {
        return Ok(stdout);
    }
    Err(BridgeError::EngineFailed {
        code: output.status.code(),
        details: stdout,
    })
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
    let input_path = input_file.path().to_string_lossy().into_owned();
    let mut receiver = {
        let mut running = engine.lock()?;
        if running.is_some() {
            return Err(BridgeError::RunInProgress);
        }
        let (receiver, child) = app
            .shell()
            .sidecar(SIDECAR_NAME)?
            .args(["run", module_id.as_str(), "--input", input_path.as_str()])
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
