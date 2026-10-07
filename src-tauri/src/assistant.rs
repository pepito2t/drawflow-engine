use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, MutexGuard};

use tauri::{ipc::Channel, AppHandle, Manager, State};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

use crate::access::AccessLock;
use crate::error::BridgeError;
use crate::paths::settings_file;
use crate::runs::Killable;
use crate::sidecar::{path_argument, relay_events, write_input_file, EngineMessage, SIDECAR_NAME};

/// The assistant answers one question at a time; its process is kept to stop it on demand.
#[derive(Default)]
pub struct AssistantTurn {
    turn: Mutex<Option<(u64, CommandChild)>>,
    next_id: AtomicU64,
}

impl AssistantTurn {
    fn begin<T>(
        &self,
        spawn: impl FnOnce() -> Result<(T, CommandChild), BridgeError>,
    ) -> Result<(u64, T), BridgeError> {
        let mut turn = self.lock()?;
        if turn.is_some() {
            return Err(BridgeError::AssistantBusy);
        }
        let (handle, child) = spawn()?;
        let turn_id = self.next_id.fetch_add(1, Ordering::Relaxed);
        *turn = Some((turn_id, child));
        Ok((turn_id, handle))
    }

    fn end(&self, turn_id: u64) -> Result<(), BridgeError> {
        let mut turn = self.lock()?;
        if turn.as_ref().is_some_and(|(id, _)| *id == turn_id) {
            *turn = None;
        }
        Ok(())
    }

    pub fn stop(&self) -> Result<(), BridgeError> {
        match self.lock()?.take() {
            Some((_, child)) => child.kill_process(),
            None => Ok(()),
        }
    }

    fn lock(&self) -> Result<MutexGuard<'_, Option<(u64, CommandChild)>>, BridgeError> {
        self.turn.lock().map_err(|_| BridgeError::StatePoisoned)
    }
}

#[tauri::command]
pub fn assistant_chat(
    app: AppHandle,
    assistant: State<'_, AssistantTurn>,
    lock: State<'_, AccessLock>,
    conversation: serde_json::Value,
    on_event: Channel<EngineMessage>,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    let input_file = write_input_file(&conversation)?;
    let arguments = chat_arguments(
        path_argument(settings_file(&app)?),
        path_argument(input_file.path().to_path_buf()),
    );
    let (turn_id, mut receiver) =
        assistant.begin(|| Ok(app.shell().sidecar(SIDECAR_NAME)?.args(arguments).spawn()?))?;
    tauri::async_runtime::spawn(async move {
        if let Err(error) = relay_events(&mut receiver, &on_event, |_| {}).await {
            eprintln!("Relais de l'assistant interrompu : {error}");
        }
        if let Err(error) = app.state::<AssistantTurn>().end(turn_id) {
            eprintln!("Fin de réponse de l'assistant non enregistrée : {error}");
        }
        drop(input_file);
    });
    Ok(())
}

#[tauri::command]
pub fn assistant_cancel(
    assistant: State<'_, AssistantTurn>,
    lock: State<'_, AccessLock>,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    assistant.stop()
}

fn chat_arguments(settings: String, input: String) -> Vec<String> {
    vec![
        "assistant".to_owned(),
        "chat".to_owned(),
        "--settings".to_owned(),
        settings,
        "--input".to_owned(),
        input,
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn chat_arguments_pass_settings_and_conversation_files() {
        assert_eq!(
            chat_arguments("C:\\cfg é\\settings.json".to_owned(), "q.json".to_owned()),
            [
                "assistant",
                "chat",
                "--settings",
                "C:\\cfg é\\settings.json",
                "--input",
                "q.json"
            ]
        );
    }
}
