pub mod config;
pub mod protocol;
pub mod server;

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex, MutexGuard};
use std::time::Duration;

use serde::Serialize;
use tauri::{AppHandle, Emitter, Manager, State};
use tokio::sync::{broadcast, oneshot};

use crate::access::AccessLock;
use crate::error::BridgeError;
use config::IntegrationConfig;
use protocol::{CommandReply, CommandRequest, ServerMessage};
use server::{Dispatcher, ReplyFuture, ServerHandle};

const COMMAND_EVENT: &str = "integration-command";
const REPLY_TIMEOUT: Duration = Duration::from_secs(15);
const EVENT_BUFFER: usize = 256;
const NO_REPLY_MESSAGE: &str = "Drawflow n'a pas répondu à temps.";
/// Below this range the OS reserves the ports; 0 would pick a random one the plugin cannot find.
const MIN_PORT: u16 = 1024;

#[derive(Clone, Debug, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct IntegrationStatus {
    enabled: bool,
    port: u16,
    token: String,
    address: Option<String>,
    error: Option<String>,
}

pub struct IntegrationState {
    events: broadcast::Sender<String>,
    pending: Arc<Mutex<HashMap<String, oneshot::Sender<CommandReply>>>>,
    server: tauri::async_runtime::Mutex<Option<ServerHandle>>,
    last_error: Mutex<Option<String>>,
    next_request: AtomicU64,
}

impl Default for IntegrationState {
    fn default() -> Self {
        let (events, _) = broadcast::channel(EVENT_BUFFER);
        Self {
            events,
            pending: Arc::default(),
            server: tauri::async_runtime::Mutex::new(None),
            last_error: Mutex::new(None),
            next_request: AtomicU64::new(1),
        }
    }
}

impl IntegrationState {
    pub fn broadcast(&self, message: &ServerMessage) {
        if let Ok(json) = serde_json::to_string(message) {
            // An error only means no client is connected right now.
            let _no_subscriber = self.events.send(json);
        }
    }

    fn pending(
        &self,
    ) -> Result<MutexGuard<'_, HashMap<String, oneshot::Sender<CommandReply>>>, BridgeError> {
        self.pending.lock().map_err(|_| BridgeError::StatePoisoned)
    }

    fn set_error(&self, error: Option<String>) {
        if let Ok(mut last) = self.last_error.lock() {
            *last = error;
        }
    }
}

/// Forwards local API commands to the UI, which owns every action (named commands).
struct AppDispatcher {
    app: AppHandle,
}

impl Dispatcher for AppDispatcher {
    fn is_locked(&self) -> bool {
        self.app.state::<AccessLock>().ensure_unlocked().is_err()
    }

    fn dispatch(&self, request: CommandRequest) -> ReplyFuture<'_> {
        Box::pin(dispatch_to_ui(&self.app, request))
    }
}

/// Sends a named command to the UI and waits for its reply, as the local API does.
pub async fn dispatch_to_ui(app: &AppHandle, request: CommandRequest) -> CommandReply {
    let state = app.state::<IntegrationState>();
    let ticket = format!(
        "{}-{}",
        state.next_request.fetch_add(1, Ordering::Relaxed),
        request.id
    );
    let (sender, receiver) = oneshot::channel();
    match state.pending() {
        Ok(mut pending) => {
            pending.insert(ticket.clone(), sender);
        }
        Err(error) => return CommandReply::failure(request.id, error.to_string()),
    }
    let forwarded = CommandRequest {
        id: ticket.clone(),
        ..request.clone()
    };
    if let Err(error) = app.emit(COMMAND_EVENT, forwarded) {
        return CommandReply::failure(request.id, error.to_string());
    }
    let reply = tokio::time::timeout(REPLY_TIMEOUT, receiver).await;
    if let Ok(mut pending) = state.pending() {
        pending.remove(&ticket);
    }
    match reply {
        Ok(Ok(reply)) => CommandReply {
            id: request.id,
            ..reply
        },
        _ => CommandReply::failure(request.id, NO_REPLY_MESSAGE),
    }
}

pub async fn apply(app: &AppHandle, config: &IntegrationConfig) {
    let state = app.state::<IntegrationState>();
    let mut server = state.server.lock().await;
    if let Some(previous) = server.take() {
        previous.stop().await;
    }
    if !config.enabled {
        state.set_error(None);
        return;
    }
    let dispatcher = Arc::new(AppDispatcher { app: app.clone() });
    match server::start(
        config.port,
        config.token.clone(),
        dispatcher,
        state.events.clone(),
    )
    .await
    {
        Ok(handle) => {
            *server = Some(handle);
            state.set_error(None);
        }
        Err(error) => state.set_error(Some(format!(
            "Port {} indisponible : {error}. Choisissez un autre port.",
            config.port
        ))),
    }
}

/// The Stream Dock plugin reads Drawflow's API settings itself: installing it must turn the API on.
pub async fn ensure_enabled(app: &AppHandle) -> Result<(), BridgeError> {
    let path = config::config_file(app)?;
    if let Some(enabled) = enabling(config::load(&path)?) {
        config::save(&path, &enabled)?;
        apply(app, &enabled).await;
    }
    Ok(())
}

fn enabling(config: IntegrationConfig) -> Option<IntegrationConfig> {
    if config.enabled {
        return None;
    }
    Some(IntegrationConfig {
        enabled: true,
        ..config
    })
}

/// A corrupt configuration must not keep the application from starting: the API stays off and
/// the status reports why.
pub fn start_at_launch(app: &AppHandle) -> Result<(), BridgeError> {
    let config = match config::load(&config::config_file(app)?) {
        Ok(config) => config,
        Err(error) => {
            app.state::<IntegrationState>()
                .set_error(Some(error.to_string()));
            return Ok(());
        }
    };
    let handle = app.clone();
    tauri::async_runtime::spawn(async move { apply(&handle, &config).await });
    Ok(())
}

#[tauri::command]
pub async fn integration_status(
    app: AppHandle,
    state: State<'_, IntegrationState>,
    lock: State<'_, AccessLock>,
) -> Result<IntegrationStatus, BridgeError> {
    lock.ensure_unlocked()?;
    let config = config::load(&config::config_file(&app)?)?;
    let address = state
        .server
        .lock()
        .await
        .as_ref()
        .map(|server| server.address.to_string());
    let error = state
        .last_error
        .lock()
        .map_err(|_| BridgeError::StatePoisoned)?
        .clone();
    Ok(IntegrationStatus {
        enabled: config.enabled,
        port: config.port,
        token: config.token,
        address,
        error,
    })
}

#[tauri::command]
pub async fn integration_update(
    app: AppHandle,
    lock: State<'_, AccessLock>,
    enabled: bool,
    port: u16,
    regenerate_token: bool,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    if port < MIN_PORT {
        return Err(BridgeError::InvalidPort(port));
    }
    let path = config::config_file(&app)?;
    let mut updated = config::load(&path)?;
    updated.enabled = enabled;
    updated.port = port;
    if regenerate_token {
        updated.token = config::generate_token();
    }
    config::save(&path, &updated)?;
    apply(&app, &updated).await;
    Ok(())
}

#[tauri::command]
pub fn integration_reply(
    state: State<'_, IntegrationState>,
    reply: CommandReply,
) -> Result<(), BridgeError> {
    if let Some(sender) = state.pending()?.remove(&reply.id) {
        // The requester may have timed out; nothing else to notify.
        let _requester_gone = sender.send(reply);
    }
    Ok(())
}

#[tauri::command]
pub fn integration_publish(
    state: State<'_, IntegrationState>,
    lock: State<'_, AccessLock>,
    event: serde_json::Value,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    state.broadcast(&ServerMessage::Event { event });
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn installing_the_plugin_only_turns_a_disabled_api_on() {
        let disabled = IntegrationConfig {
            enabled: false,
            port: 51717,
            token: "secret".to_owned(),
        };
        let enabled = IntegrationConfig {
            enabled: true,
            ..disabled.clone()
        };

        assert_eq!(enabling(disabled), Some(enabled.clone()));
        assert_eq!(enabling(enabled), None);
    }
}
