//! Local API protocol (version 1), documented in docs/api-locale.md.

use serde::{Deserialize, Serialize};
use subtle::ConstantTimeEq;

use crate::error::BridgeError;

pub const PROTOCOL_VERSION: u32 = 1;

#[derive(Debug, Deserialize, PartialEq)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum ClientMessage {
    Hello {
        token: String,
        version: u32,
    },
    Command {
        id: String,
        command: String,
        #[serde(default)]
        args: serde_json::Value,
    },
}

#[derive(Debug, Serialize, PartialEq)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum ServerMessage {
    Welcome { version: u32, locked: bool },
    Result(CommandReply),
    Event { event: serde_json::Value },
    Locked { locked: bool },
    Error { code: String, message: String },
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct CommandReply {
    pub id: String,
    pub ok: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub code: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
}

impl CommandReply {
    pub fn failure(id: String, code: &str, message: impl Into<String>) -> Self {
        Self {
            id,
            ok: false,
            code: Some(code.to_owned()),
            error: Some(message.into()),
            data: None,
        }
    }

    pub fn from_error(id: String, error: &BridgeError) -> Self {
        Self::failure(id, error.code(), error.to_string())
    }
}

#[derive(Clone, Debug, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct CommandRequest {
    pub id: String,
    pub command: String,
    pub args: serde_json::Value,
}

/// Compares secrets without leaking their content through timing.
pub fn tokens_match(expected: &str, received: &str) -> bool {
    expected.as_bytes().ct_eq(received.as_bytes()).into()
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    #[test]
    fn parses_hello_and_command() {
        let hello: ClientMessage =
            serde_json::from_str(r#"{"type":"hello","token":"t","version":1}"#).unwrap();
        assert_eq!(
            hello,
            ClientMessage::Hello {
                token: "t".to_owned(),
                version: 1
            }
        );
        let command: ClientMessage =
            serde_json::from_str(r#"{"type":"command","id":"1","command":"runs.cancel-all"}"#)
                .unwrap();
        assert_eq!(
            command,
            ClientMessage::Command {
                id: "1".to_owned(),
                command: "runs.cancel-all".to_owned(),
                args: serde_json::Value::Null
            }
        );
    }

    #[test]
    fn serializes_server_messages_with_type_tag() {
        let welcome = serde_json::to_string(&ServerMessage::Welcome {
            version: 1,
            locked: false,
        })
        .unwrap();
        assert_eq!(welcome, r#"{"type":"welcome","version":1,"locked":false}"#);
        let failure = serde_json::to_value(ServerMessage::Result(CommandReply::failure(
            "7".to_owned(),
            "locked",
            "Drawflow is locked.",
        )))
        .unwrap();
        assert_eq!(
            failure,
            serde_json::json!({
                "type": "result",
                "id": "7",
                "ok": false,
                "code": "locked",
                "error": "Drawflow is locked."
            })
        );
    }

    #[test]
    fn server_errors_carry_a_code_next_to_the_message() {
        let error = serde_json::to_value(ServerMessage::Error {
            code: "unknownMessage".to_owned(),
            message: "Unrecognized message.".to_owned(),
        })
        .unwrap();
        assert_eq!(
            error,
            serde_json::json!({
                "type": "error",
                "code": "unknownMessage",
                "message": "Unrecognized message."
            })
        );
    }

    #[test]
    fn bridge_errors_become_coded_failures() {
        let reply = CommandReply::from_error("3".to_owned(), &BridgeError::StatePoisoned);
        assert_eq!(reply.code.as_deref(), Some("statePoisoned"));
        assert_eq!(
            reply.error.as_deref(),
            Some("Internal application state unavailable. Restart Drawflow.")
        );
    }

    #[test]
    fn replies_from_the_ui_may_omit_the_code() {
        let reply: CommandReply =
            serde_json::from_str(r#"{"id":"1","ok":false,"error":"Préréglage introuvable."}"#)
                .unwrap();
        assert_eq!(reply.code, None);
    }

    #[test]
    fn token_comparison_requires_exact_match() {
        assert!(tokens_match("abc123", "abc123"));
        assert!(!tokens_match("abc123", "abc124"));
        assert!(!tokens_match("abc123", "abc12"));
    }
}
