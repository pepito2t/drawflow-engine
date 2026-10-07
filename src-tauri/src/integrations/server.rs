use std::future::Future;
use std::io;
use std::net::{Ipv4Addr, SocketAddr};
use std::pin::Pin;
use std::sync::Arc;
use std::time::{Duration, Instant};

use futures_util::{SinkExt, StreamExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::{broadcast, mpsc, oneshot, watch, OwnedSemaphorePermit, Semaphore};
use tokio_tungstenite::tungstenite::handshake::server::{ErrorResponse, Request, Response};
use tokio_tungstenite::tungstenite::http::{header::ORIGIN, StatusCode};
use tokio_tungstenite::tungstenite::protocol::WebSocketConfig;
use tokio_tungstenite::tungstenite::Message;
use tokio_tungstenite::WebSocketStream;

use super::protocol::{
    tokens_match, ClientMessage, CommandReply, CommandRequest, ServerMessage, PROTOCOL_VERSION,
};

const HELLO_TIMEOUT: Duration = Duration::from_secs(5);
const KEEPALIVE_INTERVAL: Duration = Duration::from_secs(30);
const SILENT_PERIODS_BEFORE_CLOSE: u32 = 2;
const MAX_MESSAGE_BYTES: usize = 64 * 1024;
const MAX_CLIENTS: usize = 8;
const LOCKED_CODE: &str = "locked";
const LOCKED_MESSAGE: &str = "Drawflow is locked: enter the access code in the application.";
const INVALID_TOKEN_CODE: &str = "invalidToken";
const INVALID_TOKEN_MESSAGE: &str = "Invalid token or protocol version.";
const UNKNOWN_MESSAGE_CODE: &str = "unknownMessage";
const UNKNOWN_MESSAGE_MESSAGE: &str = "Unrecognized message.";
const RESYNC_EVENT_TYPE: &str = "resync";

pub type ReplyFuture<'a> = Pin<Box<dyn Future<Output = CommandReply> + Send + 'a>>;

/// Executes commands on behalf of the server; implemented by the app (and by fakes in tests).
pub trait Dispatcher: Send + Sync + 'static {
    fn is_locked(&self) -> bool;
    fn dispatch(&self, request: CommandRequest) -> ReplyFuture<'_>;
}

#[derive(Clone, Copy)]
struct Limits {
    max_message_bytes: usize,
    max_clients: usize,
    keepalive: Duration,
}

impl Default for Limits {
    fn default() -> Self {
        Self {
            max_message_bytes: MAX_MESSAGE_BYTES,
            max_clients: MAX_CLIENTS,
            keepalive: KEEPALIVE_INTERVAL,
        }
    }
}

pub struct ServerHandle {
    pub address: SocketAddr,
    shutdown: watch::Sender<bool>,
    listener_closed: Option<oneshot::Receiver<()>>,
}

impl ServerHandle {
    /// Resolves once the listening socket is released, so the same port can be bound again at
    /// once (Windows does not set SO_REUSEADDR on listeners).
    pub async fn stop(mut self) {
        self.shutdown.send_replace(true);
        if let Some(closed) = self.listener_closed.take() {
            let _accept_task_gone = closed.await;
        }
    }
}

impl Drop for ServerHandle {
    fn drop(&mut self) {
        self.shutdown.send_replace(true);
    }
}

/// Listens on 127.0.0.1 only: the API is never reachable from the network.
pub async fn start<D: Dispatcher>(
    port: u16,
    token: String,
    dispatcher: Arc<D>,
    events: broadcast::Sender<String>,
) -> io::Result<ServerHandle> {
    start_with_limits(port, token, dispatcher, events, Limits::default()).await
}

async fn start_with_limits<D: Dispatcher>(
    port: u16,
    token: String,
    dispatcher: Arc<D>,
    events: broadcast::Sender<String>,
    limits: Limits,
) -> io::Result<ServerHandle> {
    let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, port)).await?;
    let address = listener.local_addr()?;
    let (shutdown, mut stop) = watch::channel(false);
    let (closed_sender, listener_closed) = oneshot::channel();
    let token = Arc::new(token);
    let seats = Arc::new(Semaphore::new(limits.max_clients));
    tokio::spawn(async move {
        loop {
            tokio::select! {
                _ = stop.changed() => break,
                accepted = listener.accept() => {
                    let Ok((stream, _)) = accepted else { continue };
                    // Beyond the cap the connection is simply dropped: no handshake, no task.
                    let Ok(seat) = Arc::clone(&seats).try_acquire_owned() else { continue };
                    let client = Client {
                        token: Arc::clone(&token),
                        dispatcher: Arc::clone(&dispatcher),
                        events: events.subscribe(),
                        stop: stop.clone(),
                        limits,
                        _seat: seat,
                    };
                    tokio::spawn(client.serve(stream));
                }
            }
        }
        drop(listener);
        let _nobody_waiting = closed_sender.send(());
    });
    Ok(ServerHandle {
        address,
        shutdown,
        listener_closed: Some(listener_closed),
    })
}

/// Browsers always send `Origin`; local tools never do. Refusing it keeps web pages from even
/// attempting the token.
// The signature is imposed by tungstenite's `Callback` trait.
#[allow(clippy::result_large_err)]
fn reject_browsers(request: &Request, response: Response) -> Result<Response, ErrorResponse> {
    if !request.headers().contains_key(ORIGIN) {
        return Ok(response);
    }
    let mut refusal = ErrorResponse::new(None);
    *refusal.status_mut() = StatusCode::FORBIDDEN;
    Err(refusal)
}

struct Client<D: Dispatcher> {
    token: Arc<String>,
    dispatcher: Arc<D>,
    events: broadcast::Receiver<String>,
    stop: watch::Receiver<bool>,
    limits: Limits,
    _seat: OwnedSemaphorePermit,
}

impl<D: Dispatcher> Client<D> {
    async fn serve(mut self, stream: TcpStream) {
        let config = WebSocketConfig::default()
            .max_message_size(Some(self.limits.max_message_bytes))
            .max_frame_size(Some(self.limits.max_message_bytes));
        let handshake =
            tokio_tungstenite::accept_hdr_async_with_config(stream, reject_browsers, Some(config));
        let Ok(mut socket) = handshake.await else {
            return;
        };
        if !self.authenticate(&mut socket).await {
            let message = ServerMessage::Error {
                code: INVALID_TOKEN_CODE.to_owned(),
                message: INVALID_TOKEN_MESSAGE.to_owned(),
            };
            let _closing = send(&mut socket, &message).await;
            return;
        }
        let welcome = ServerMessage::Welcome {
            version: PROTOCOL_VERSION,
            locked: self.dispatcher.is_locked(),
        };
        if send(&mut socket, &welcome).await.is_err() {
            return;
        }
        self.relay(socket).await;
    }

    async fn authenticate(&self, socket: &mut WebSocketStream<TcpStream>) -> bool {
        let Ok(Some(Ok(Message::Text(text)))) =
            tokio::time::timeout(HELLO_TIMEOUT, socket.next()).await
        else {
            return false;
        };
        matches!(
            serde_json::from_str::<ClientMessage>(&text),
            Ok(ClientMessage::Hello { token, version })
                if version == PROTOCOL_VERSION && tokens_match(&self.token, &token)
        )
    }

    /// Commands run in their own task so events keep flowing while the app answers.
    async fn relay(&mut self, mut socket: WebSocketStream<TcpStream>) {
        let (replies, mut pending) = mpsc::unbounded_channel::<ServerMessage>();
        let keepalive = self.limits.keepalive;
        let mut ticker =
            tokio::time::interval_at(tokio::time::Instant::now() + keepalive, keepalive);
        let mut last_heard = Instant::now();
        loop {
            tokio::select! {
                _ = self.stop.changed() => break,
                event = self.events.recv() => {
                    let outcome = match event {
                        Ok(json) => socket.send(Message::Text(json.into())).await,
                        Err(broadcast::error::RecvError::Lagged(_)) => send(&mut socket, &resync_event()).await,
                        Err(broadcast::error::RecvError::Closed) => break,
                    };
                    if outcome.is_err() {
                        break;
                    }
                }
                Some(reply) = pending.recv() => {
                    if send(&mut socket, &reply).await.is_err() {
                        break;
                    }
                }
                _ = ticker.tick() => {
                    if last_heard.elapsed() >= keepalive * SILENT_PERIODS_BEFORE_CLOSE {
                        break;
                    }
                    if socket.send(Message::Ping(Vec::new().into())).await.is_err() {
                        break;
                    }
                }
                incoming = socket.next() => {
                    last_heard = Instant::now();
                    match incoming {
                        Some(Ok(Message::Text(text))) => {
                            let dispatcher = Arc::clone(&self.dispatcher);
                            let replies = replies.clone();
                            tokio::spawn(async move {
                                let reply = answer(dispatcher.as_ref(), &text).await;
                                // The client may be gone by the time the app answers.
                                let _client_gone = replies.send(reply);
                            });
                        }
                        Some(Ok(Message::Close(_))) | None | Some(Err(_)) => break,
                        Some(Ok(_)) => {}
                    }
                }
            }
        }
    }
}

/// Tells the client it missed events: it should ask for the full state again.
fn resync_event() -> ServerMessage {
    ServerMessage::Event {
        event: serde_json::json!({ "type": RESYNC_EVENT_TYPE }),
    }
}

async fn answer<D: Dispatcher>(dispatcher: &D, text: &str) -> ServerMessage {
    let request = match serde_json::from_str::<ClientMessage>(text) {
        Ok(ClientMessage::Command { id, command, args }) => CommandRequest { id, command, args },
        Ok(ClientMessage::Hello { .. }) | Err(_) => {
            return ServerMessage::Error {
                code: UNKNOWN_MESSAGE_CODE.to_owned(),
                message: UNKNOWN_MESSAGE_MESSAGE.to_owned(),
            }
        }
    };
    if dispatcher.is_locked() {
        return ServerMessage::Result(CommandReply::failure(
            request.id,
            LOCKED_CODE,
            LOCKED_MESSAGE,
        ));
    }
    ServerMessage::Result(dispatcher.dispatch(request).await)
}

async fn send(
    socket: &mut WebSocketStream<TcpStream>,
    message: &ServerMessage,
) -> Result<(), tokio_tungstenite::tungstenite::Error> {
    let json = serde_json::to_string(message)
        .map_err(|error| tokio_tungstenite::tungstenite::Error::Io(io::Error::other(error)))?;
    socket.send(Message::Text(json.into())).await
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use std::sync::atomic::{AtomicBool, Ordering};

    use super::*;
    use tokio::sync::Notify;
    use tokio_tungstenite::connect_async;
    use tokio_tungstenite::tungstenite::client::IntoClientRequest;

    type ClientSocket = WebSocketStream<tokio_tungstenite::MaybeTlsStream<TcpStream>>;

    const TEST_TIMEOUT: Duration = Duration::from_secs(5);

    struct FakeApp {
        locked: AtomicBool,
        release: Option<Arc<Notify>>,
    }

    impl Dispatcher for FakeApp {
        fn is_locked(&self) -> bool {
            self.locked.load(Ordering::SeqCst)
        }

        fn dispatch(&self, request: CommandRequest) -> ReplyFuture<'_> {
            Box::pin(async move {
                if let Some(release) = &self.release {
                    release.notified().await;
                }
                CommandReply {
                    id: request.id,
                    ok: true,
                    code: None,
                    error: None,
                    data: Some(serde_json::json!({ "echo": request.command })),
                }
            })
        }
    }

    async fn server(locked: bool) -> (ServerHandle, broadcast::Sender<String>) {
        let (events, _) = broadcast::channel(16);
        let handle = start(
            0,
            "secret".to_owned(),
            fake_app(locked, None),
            events.clone(),
        )
        .await
        .unwrap();
        (handle, events)
    }

    fn fake_app(locked: bool, release: Option<Arc<Notify>>) -> Arc<FakeApp> {
        Arc::new(FakeApp {
            locked: AtomicBool::new(locked),
            release,
        })
    }

    async fn connect(handle: &ServerHandle, token: &str) -> ClientSocket {
        let url = format!("ws://{}", handle.address);
        let (mut socket, _) = connect_async(url).await.unwrap();
        let hello = serde_json::json!({ "type": "hello", "token": token, "version": 1 });
        send_text(&mut socket, hello).await;
        socket
    }

    async fn send_text(socket: &mut ClientSocket, payload: serde_json::Value) {
        socket
            .send(Message::Text(payload.to_string().into()))
            .await
            .unwrap();
    }

    async fn next_json(socket: &mut ClientSocket) -> serde_json::Value {
        loop {
            if let Message::Text(text) = socket.next().await.unwrap().unwrap() {
                return serde_json::from_str(&text).unwrap();
            }
        }
    }

    async fn drain(socket: &mut ClientSocket) -> Vec<Message> {
        let mut received = Vec::new();
        while let Some(Ok(message)) = socket.next().await {
            received.push(message);
        }
        received
    }

    #[tokio::test]
    async fn listens_on_loopback_only() {
        let (handle, _) = server(false).await;
        assert!(handle.address.ip().is_loopback());
    }

    #[tokio::test]
    async fn wrong_token_is_refused() {
        let (handle, _) = server(false).await;
        let mut socket = connect(&handle, "wrong").await;
        let refusal = next_json(&mut socket).await;
        assert_eq!(refusal["type"], "error");
        assert_eq!(refusal["code"], INVALID_TOKEN_CODE);
        assert_eq!(refusal["message"], INVALID_TOKEN_MESSAGE);
    }

    #[tokio::test]
    async fn commands_are_dispatched_and_answered() {
        let (handle, _) = server(false).await;
        let mut socket = connect(&handle, "secret").await;
        assert_eq!(next_json(&mut socket).await["type"], "welcome");
        let command = serde_json::json!({ "type": "command", "id": "42", "command": "tab.open" });
        send_text(&mut socket, command).await;
        let reply = next_json(&mut socket).await;
        assert_eq!(reply["id"], "42");
        assert_eq!(reply["ok"], true);
        assert_eq!(reply["data"]["echo"], "tab.open");
    }

    #[tokio::test]
    async fn locked_app_refuses_commands() {
        let (handle, _) = server(true).await;
        let mut socket = connect(&handle, "secret").await;
        assert_eq!(next_json(&mut socket).await["locked"], true);
        let command = serde_json::json!({ "type": "command", "id": "1", "command": "preset.run" });
        send_text(&mut socket, command).await;
        let reply = next_json(&mut socket).await;
        assert_eq!(reply["ok"], false);
        assert_eq!(reply["code"], LOCKED_CODE);
        assert_eq!(reply["error"], LOCKED_MESSAGE);
    }

    #[tokio::test]
    async fn unknown_message_is_answered_with_its_code() {
        let (handle, _) = server(false).await;
        let mut socket = connect(&handle, "secret").await;
        next_json(&mut socket).await;
        send_text(&mut socket, serde_json::json!({ "type": "bogus" })).await;
        let error = next_json(&mut socket).await;
        assert_eq!(error["type"], "error");
        assert_eq!(error["code"], UNKNOWN_MESSAGE_CODE);
    }

    #[tokio::test]
    async fn app_events_are_broadcast() {
        let (handle, events) = server(false).await;
        let mut socket = connect(&handle, "secret").await;
        next_json(&mut socket).await;
        events
            .send(r#"{"type":"event","event":{"type":"settingsSaved"}}"#.to_owned())
            .unwrap();
        assert_eq!(
            next_json(&mut socket).await["event"]["type"],
            "settingsSaved"
        );
    }

    #[tokio::test]
    async fn port_is_free_again_as_soon_as_stop_returns() {
        let (events, _) = broadcast::channel(16);
        let first = start(
            0,
            "secret".to_owned(),
            fake_app(false, None),
            events.clone(),
        )
        .await
        .unwrap();
        let port = first.address.port();
        first.stop().await;
        for _ in 0..10 {
            let handle = start(
                port,
                "secret".to_owned(),
                fake_app(false, None),
                events.clone(),
            )
            .await
            .unwrap();
            assert_eq!(handle.address.port(), port);
            handle.stop().await;
        }
    }

    #[tokio::test]
    async fn handshake_with_origin_header_is_refused() {
        let (handle, _) = server(false).await;
        let mut request = format!("ws://{}", handle.address)
            .into_client_request()
            .unwrap();
        request
            .headers_mut()
            .insert(ORIGIN, "http://evil.example".parse().unwrap());
        let error = connect_async(request).await.err().unwrap();
        match error {
            tokio_tungstenite::tungstenite::Error::Http(response) => {
                assert_eq!(response.status(), StatusCode::FORBIDDEN);
            }
            other => panic!("expected an HTTP refusal, got {other:?}"),
        }
    }

    #[tokio::test]
    async fn oversized_message_closes_the_connection() {
        let (handle, _) = server(false).await;
        let mut socket = connect(&handle, "secret").await;
        next_json(&mut socket).await;
        let oversized = "x".repeat(MAX_MESSAGE_BYTES + 1);
        socket.send(Message::Text(oversized.into())).await.unwrap();
        let received = tokio::time::timeout(TEST_TIMEOUT, drain(&mut socket))
            .await
            .unwrap();
        assert!(received.iter().all(|message| !message.is_text()));
    }

    #[tokio::test]
    async fn ninth_connection_is_dropped() {
        let (handle, _) = server(false).await;
        let url = format!("ws://{}", handle.address);
        let mut seated = Vec::new();
        for _ in 0..MAX_CLIENTS {
            seated.push(connect_async(&url).await.unwrap());
        }
        let refused = tokio::time::timeout(TEST_TIMEOUT, connect_async(&url))
            .await
            .unwrap();
        assert!(refused.is_err());
    }

    #[tokio::test]
    async fn events_keep_flowing_while_a_command_waits() {
        let (events, _) = broadcast::channel(16);
        let release = Arc::new(Notify::new());
        let app = fake_app(false, Some(Arc::clone(&release)));
        let handle = start(0, "secret".to_owned(), app, events.clone())
            .await
            .unwrap();
        let mut socket = connect(&handle, "secret").await;
        next_json(&mut socket).await;
        let command =
            serde_json::json!({ "type": "command", "id": "slow", "command": "mail.fetch" });
        send_text(&mut socket, command).await;
        events
            .send(r#"{"type":"event","event":{"type":"runProgress"}}"#.to_owned())
            .unwrap();
        let event = tokio::time::timeout(TEST_TIMEOUT, next_json(&mut socket))
            .await
            .unwrap();
        assert_eq!(event["event"]["type"], "runProgress");
        release.notify_one();
        let reply = next_json(&mut socket).await;
        assert_eq!(reply["id"], "slow");
        assert_eq!(reply["ok"], true);
    }

    #[tokio::test]
    async fn lagging_client_receives_a_resync_event() {
        let (events, _) = broadcast::channel(2);
        let handle = start(
            0,
            "secret".to_owned(),
            fake_app(false, None),
            events.clone(),
        )
        .await
        .unwrap();
        let mut socket = connect(&handle, "secret").await;
        next_json(&mut socket).await;
        for index in 0..5 {
            events
                .send(format!(
                    r#"{{"type":"event","event":{{"type":"e{index}"}}}}"#
                ))
                .unwrap();
        }
        let mut types = Vec::new();
        for _ in 0..3 {
            let received = tokio::time::timeout(TEST_TIMEOUT, next_json(&mut socket))
                .await
                .unwrap();
            types.push(received["event"]["type"].as_str().unwrap().to_owned());
        }
        assert!(
            types.contains(&RESYNC_EVENT_TYPE.to_owned()),
            "expected a resync among {types:?}"
        );
    }

    #[tokio::test]
    async fn silent_client_is_pinged_then_dropped() {
        let (events, _) = broadcast::channel(16);
        let limits = Limits {
            keepalive: Duration::from_millis(50),
            ..Limits::default()
        };
        let handle = start_with_limits(
            0,
            "secret".to_owned(),
            fake_app(false, None),
            events,
            limits,
        )
        .await
        .unwrap();
        let mut socket = connect(&handle, "secret").await;
        next_json(&mut socket).await;
        tokio::time::sleep(limits.keepalive * (SILENT_PERIODS_BEFORE_CLOSE + 2)).await;
        let received = tokio::time::timeout(TEST_TIMEOUT, drain(&mut socket))
            .await
            .unwrap();
        assert!(received.iter().any(Message::is_ping));
    }
}
