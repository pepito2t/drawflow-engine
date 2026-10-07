//! Local API protocol (version 1), documented in docs/api-locale.md.

use serde::{Deserialize, Serialize};
use subtle::ConstantTimeEq;

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
    Error { message: String },
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct CommandReply {
    pub id: String,
    pub ok: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
}

impl CommandReply {
    pub fn failure(id: String, message: impl Into<String>) -> Self {
        Self {
            id,
            ok: false,
            error: Some(message.into()),
            data: None,
        }
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
            "verrouillée",
        )))
        .unwrap();
        assert_eq!(failure["type"], "result");
        assert_eq!(failure["error"], "verrouillée");
    }

    #[test]
    fn token_comparison_requires_exact_match() {
        assert!(tokens_match("abc123", "abc123"));
        assert!(!tokens_match("abc123", "abc124"));
        assert!(!tokens_match("abc123", "abc12"));
    }
}
