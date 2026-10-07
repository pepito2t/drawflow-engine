use std::future::Future;
use std::io;
use std::net::{Ipv4Addr, SocketAddr};
use std::pin::Pin;
use std::sync::Arc;
use std::time::Duration;

use futures_util::{SinkExt, StreamExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::{broadcast, watch};
use tokio_tungstenite::tungstenite::Message;
use tokio_tungstenite::WebSocketStream;

use super::protocol::{
    tokens_match, ClientMessage, CommandReply, CommandRequest, ServerMessage, PROTOCOL_VERSION,
};

const HELLO_TIMEOUT: Duration = Duration::from_secs(5);
const LOCKED_MESSAGE: &str =
    "Drawflow est verrouillée : saisissez le code d'accès dans l'application.";

pub type ReplyFuture<'a> = Pin<Box<dyn Future<Output = CommandReply> + Send + 'a>>;

/// Executes commands on behalf of the server; implemented by the app (and by fakes in tests).
pub trait Dispatcher: Send + Sync + 'static {
    fn is_locked(&self) -> bool;
    fn dispatch(&self, request: CommandRequest) -> ReplyFuture<'_>;
}

pub struct ServerHandle {
    pub address: SocketAddr,
    shutdown: watch::Sender<bool>,
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
    let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, port)).await?;
    let address = listener.local_addr()?;
    let (shutdown, mut stop) = watch::channel(false);
    let token = Arc::new(token);
    tokio::spawn(async move {
        loop {
            tokio::select! {
                _ = stop.changed() => break,
                accepted = listener.accept() => {
                    if let Ok((stream, _)) = accepted {
                        let client = Client {
                            token: Arc::clone(&token),
                            dispatcher: Arc::clone(&dispatcher),
                            events: events.subscribe(),
                            stop: stop.clone(),
                        };
                        tokio::spawn(client.serve(stream));
                    }
                }
            }
        }
    });
    Ok(ServerHandle { address, shutdown })
}

struct Client<D: Dispatcher> {
    token: Arc<String>,
    dispatcher: Arc<D>,
    events: broadcast::Receiver<String>,
    stop: watch::Receiver<bool>,
}

impl<D: Dispatcher> Client<D> {
    async fn serve(mut self, stream: TcpStream) {
        let Ok(mut socket) = tokio_tungstenite::accept_async(stream).await else {
            return;
        };
        if !self.authenticate(&mut socket).await {
            let message = ServerMessage::Error {
                message: "Jeton ou version de protocole invalide.".to_owned(),
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

    async fn relay(&mut self, mut socket: WebSocketStream<TcpStream>) {
        loop {
            tokio::select! {
                _ = self.stop.changed() => break,
                event = self.events.recv() => match event {
                    Ok(json) => {
                        if socket.send(Message::Text(json.into())).await.is_err() {
                            break;
                        }
                    }
                    Err(broadcast::error::RecvError::Lagged(_)) => continue,
                    Err(broadcast::error::RecvError::Closed) => break,
                },
                incoming = socket.next() => match incoming {
                    Some(Ok(Message::Text(text))) => {
                        let reply = self.answer(&text).await;
                        if send(&mut socket, &reply).await.is_err() {
                            break;
                        }
                    }
                    Some(Ok(Message::Close(_))) | None | Some(Err(_)) => break,
                    Some(Ok(_)) => continue,
                },
            }
        }
    }

    async fn answer(&self, text: &str) -> ServerMessage {
        let request = match serde_json::from_str::<ClientMessage>(text) {
            Ok(ClientMessage::Command { id, command, args }) => {
                CommandRequest { id, command, args }
            }
            Ok(ClientMessage::Hello { .. }) | Err(_) => {
                return ServerMessage::Error {
                    message: "Message non reconnu.".to_owned(),
                }
            }
        };
        if self.dispatcher.is_locked() {
            return ServerMessage::Result(CommandReply::failure(request.id, LOCKED_MESSAGE));
        }
        ServerMessage::Result(self.dispatcher.dispatch(request).await)
    }
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
    use tokio_tungstenite::connect_async;

    struct FakeApp {
        locked: AtomicBool,
    }

    impl Dispatcher for FakeApp {
        fn is_locked(&self) -> bool {
            self.locked.load(Ordering::SeqCst)
        }

        fn dispatch(&self, request: CommandRequest) -> ReplyFuture<'_> {
            Box::pin(async move {
                CommandReply {
                    id: request.id,
                    ok: true,
                    error: None,
                    data: Some(serde_json::json!({ "echo": request.command })),
                }
            })
        }
    }

    async fn server(locked: bool) -> (ServerHandle, broadcast::Sender<String>) {
        let (events, _) = broadcast::channel(16);
        let app = Arc::new(FakeApp {
            locked: AtomicBool::new(locked),
        });
        let handle = start(0, "secret".to_owned(), app, events.clone())
            .await
            .unwrap();
        (handle, events)
    }

    async fn connect(
        handle: &ServerHandle,
        token: &str,
    ) -> WebSocketStream<tokio_tungstenite::MaybeTlsStream<TcpStream>> {
        let url = format!("ws://{}", handle.address);
        let (mut socket, _) = connect_async(url).await.unwrap();
        let hello = serde_json::json!({ "type": "hello", "token": token, "version": 1 });
        socket
            .send(Message::Text(hello.to_string().into()))
            .await
            .unwrap();
        socket
    }

    async fn next_json(
        socket: &mut WebSocketStream<tokio_tungstenite::MaybeTlsStream<TcpStream>>,
    ) -> serde_json::Value {
        loop {
            if let Message::Text(text) = socket.next().await.unwrap().unwrap() {
                return serde_json::from_str(&text).unwrap();
            }
        }
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
        assert_eq!(next_json(&mut socket).await["type"], "error");
    }

    #[tokio::test]
    async fn commands_are_dispatched_and_answered() {
        let (handle, _) = server(false).await;
        let mut socket = connect(&handle, "secret").await;
        assert_eq!(next_json(&mut socket).await["type"], "welcome");
        let command = serde_json::json!({ "type": "command", "id": "42", "command": "tab.open" });
        socket
            .send(Message::Text(command.to_string().into()))
            .await
            .unwrap();
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
        socket
            .send(Message::Text(command.to_string().into()))
            .await
            .unwrap();
        let reply = next_json(&mut socket).await;
        assert_eq!(reply["ok"], false);
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
}
