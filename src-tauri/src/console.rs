use std::collections::VecDeque;
use std::sync::{Mutex, MutexGuard};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Emitter, Manager, State, WebviewUrl, WebviewWindowBuilder};

use crate::access::AccessLock;
use crate::error::BridgeError;

/// Enough for a long working session while staying a few megabytes at most.
pub const CONSOLE_CAPACITY: usize = 5000;
const MAX_MESSAGE_CHARS: usize = 2_000;
const MAX_DETAIL_CHARS: usize = 8_000;
const TRUNCATION_MARK: &str = "…";
const ENTRY_EVENT: &str = "console-entry";
const CLEARED_EVENT: &str = "console-cleared";
pub const MASK: &str = "[masqué]";
/// API tokens, hashes of secrets and most generated keys are long hexadecimal strings.
const MIN_HEX_SECRET_LENGTH: usize = 32;
const TOKEN_KEY: &str = "token";
const AUTHORIZATION_KEY: &str = "authorization";

const WINDOW_LABEL: &str = "console";
const WINDOW_URL: &str = "index.html#console";
const WINDOW_TITLE: &str = "Drawflow — Console";
const WINDOW_WIDTH: f64 = 960.0;
const WINDOW_HEIGHT: f64 = 560.0;
const WINDOW_MIN_WIDTH: f64 = 560.0;
const WINDOW_MIN_HEIGHT: f64 = 300.0;
/// Same dark background as the main window (tauri.conf.json), to avoid a white flash.
const WINDOW_BACKGROUND: tauri::window::Color = tauri::window::Color(0x11, 0x13, 0x17, 0xff);

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ConsoleLevel {
    Debug,
    Info,
    Warning,
    Error,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ConsoleSource {
    Engine,
    App,
    Bridge,
    Assistant,
    Setup,
    Rust,
}

/// What a caller reports; the log assigns the id and the time.
#[derive(Clone, Debug, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ConsoleDraft {
    pub level: ConsoleLevel,
    pub source: ConsoleSource,
    #[serde(default)]
    pub module: Option<String>,
    pub message: String,
    #[serde(default)]
    pub detail: Option<String>,
}

#[derive(Clone, Debug, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ConsoleEntry {
    id: u64,
    timestamp: u64,
    level: ConsoleLevel,
    source: ConsoleSource,
    #[serde(skip_serializing_if = "Option::is_none")]
    module: Option<String>,
    message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail: Option<String>,
}

#[derive(Default)]
struct ConsoleState {
    entries: VecDeque<ConsoleEntry>,
    next_id: u64,
    secrets: Vec<String>,
}

/// Single ring buffer shared by the main window and the detached console window.
#[derive(Default)]
pub struct ConsoleLog(Mutex<ConsoleState>);

impl ConsoleLog {
    /// Masks secrets before anything is stored: an entry is meant to be pasted into an email.
    pub fn append(&self, draft: ConsoleDraft) -> Result<ConsoleEntry, BridgeError> {
        let mut state = self.state()?;
        let secrets = &state.secrets;
        let entry = ConsoleEntry {
            id: state.next_id,
            timestamp: now_millis(),
            level: draft.level,
            source: draft.source,
            module: draft.module.map(|module| mask_secrets(&module, secrets)),
            message: truncate(&mask_secrets(&draft.message, secrets), MAX_MESSAGE_CHARS),
            detail: draft
                .detail
                .map(|detail| truncate(&mask_secrets(&detail, secrets), MAX_DETAIL_CHARS)),
        };
        state.next_id += 1;
        if state.entries.len() == CONSOLE_CAPACITY {
            state.entries.pop_front();
        }
        state.entries.push_back(entry.clone());
        Ok(entry)
    }

    pub fn entries(&self) -> Result<Vec<ConsoleEntry>, BridgeError> {
        Ok(self.state()?.entries.iter().cloned().collect())
    }

    pub fn clear(&self) -> Result<(), BridgeError> {
        self.state()?.entries.clear();
        Ok(())
    }

    /// Previous values stay masked too: an old token may still appear in a late message.
    pub fn remember_secret(&self, secret: &str) -> Result<(), BridgeError> {
        let mut state = self.state()?;
        if !secret.is_empty() && !state.secrets.iter().any(|known| known == secret) {
            state.secrets.push(secret.to_owned());
        }
        Ok(())
    }

    fn state(&self) -> Result<MutexGuard<'_, ConsoleState>, BridgeError> {
        self.0.lock().map_err(|_| BridgeError::StatePoisoned)
    }
}

/// Stores the entry and sends it to every window; a failure here is only written to stderr so
/// that logging can never loop on itself.
pub fn publish(app: &AppHandle, draft: ConsoleDraft) {
    match app.state::<ConsoleLog>().append(draft) {
        Ok(entry) => {
            if let Err(error) = app.emit(ENTRY_EVENT, &entry) {
                eprintln!("Entrée de console non diffusée : {error}");
            }
        }
        Err(error) => eprintln!("Entrée de console non enregistrée : {error}"),
    }
}

/// Bridge-side diagnostics: kept on stderr for development and shown in the console.
pub fn report(app: &AppHandle, level: ConsoleLevel, message: String) {
    eprintln!("{message}");
    publish(
        app,
        ConsoleDraft {
            level,
            source: ConsoleSource::Rust,
            module: None,
            message,
            detail: None,
        },
    );
}

/// Open while locked: errors on the lock screen are worth keeping, and nothing is read back.
#[tauri::command]
pub fn console_append(app: AppHandle, entry: ConsoleDraft) {
    publish(&app, entry);
}

#[tauri::command]
pub fn console_entries(
    log: State<'_, ConsoleLog>,
    lock: State<'_, AccessLock>,
) -> Result<Vec<ConsoleEntry>, BridgeError> {
    lock.ensure_unlocked()?;
    log.entries()
}

#[tauri::command]
pub fn console_clear(
    app: AppHandle,
    log: State<'_, ConsoleLog>,
    lock: State<'_, AccessLock>,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    log.clear()?;
    app.emit(CLEARED_EVENT, ())?;
    Ok(())
}

/// Async: creating a window from a synchronous command deadlocks on Windows.
#[tauri::command]
pub async fn console_open_window(
    app: AppHandle,
    lock: State<'_, AccessLock>,
) -> Result<(), BridgeError> {
    lock.ensure_unlocked()?;
    if let Some(window) = app.get_webview_window(WINDOW_LABEL) {
        window.unminimize()?;
        window.show()?;
        window.set_focus()?;
        return Ok(());
    }
    WebviewWindowBuilder::new(&app, WINDOW_LABEL, WebviewUrl::App(WINDOW_URL.into()))
        .title(WINDOW_TITLE)
        .inner_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        .min_inner_size(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        .theme(Some(tauri::Theme::Dark))
        .background_color(WINDOW_BACKGROUND)
        .build()?;
    Ok(())
}

/// The console window must not keep the application alive once the main window is gone.
pub fn close_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window(WINDOW_LABEL) {
        if let Err(error) = window.close() {
            eprintln!("Fermeture de la console impossible : {error}");
        }
    }
}

fn now_millis() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_or(0, |elapsed| {
            u64::try_from(elapsed.as_millis()).unwrap_or(u64::MAX)
        })
}

fn truncate(text: &str, max_chars: usize) -> String {
    match text.char_indices().nth(max_chars) {
        Some((cut, _)) => format!("{}{TRUNCATION_MARK}", &text[..cut]),
        None => text.to_owned(),
    }
}

pub fn mask_secrets(text: &str, secrets: &[String]) -> String {
    let mut masked = text.to_owned();
    for secret in secrets.iter().filter(|secret| !secret.is_empty()) {
        masked = masked.replace(secret.as_str(), MASK);
    }
    let masked = mask_assignments(&masked, AUTHORIZATION_KEY, ends_header_value);
    let masked = mask_assignments(&masked, TOKEN_KEY, ends_word_value);
    mask_hex_runs(&masked)
}

fn ends_header_value(character: char) -> bool {
    matches!(character, '\n' | '\r' | '"' | '\'')
}

fn ends_word_value(character: char) -> bool {
    character.is_whitespace() || matches!(character, '"' | '\'' | '&' | ',' | ';' | '}' | ')')
}

/// Masks the value after `key=` or `key:` (any case, optionally quoted, as in JSON).
fn mask_assignments(text: &str, key: &str, ends_value: fn(char) -> bool) -> String {
    // ASCII lowercasing keeps byte offsets, so positions found in `lower` are valid in `text`.
    let lower = text.to_ascii_lowercase();
    let mut masked = String::with_capacity(text.len());
    let mut copied_up_to = 0;
    let mut search_from = 0;
    while let Some(found) = lower[search_from..].find(key) {
        let key_end = search_from + found + key.len();
        match value_span(text, key_end, ends_value) {
            Some((start, end)) => {
                masked.push_str(&text[copied_up_to..start]);
                masked.push_str(MASK);
                copied_up_to = end;
                search_from = end;
            }
            None => search_from = key_end,
        }
    }
    masked.push_str(&text[copied_up_to..]);
    masked
}

fn value_span(text: &str, key_end: usize, ends_value: fn(char) -> bool) -> Option<(usize, usize)> {
    let rest = &text[key_end..];
    let after_quote = rest.strip_prefix(['"', '\'']).unwrap_or(rest);
    let after_separator = after_quote
        .trim_start_matches(' ')
        .strip_prefix([':', '='])?;
    let value = after_separator.trim_start_matches(' ');
    let value = value.strip_prefix(['"', '\'']).unwrap_or(value);
    let start = text.len() - value.len();
    let length = value.find(ends_value).unwrap_or(value.len());
    (length > 0).then_some((start, start + length))
}

fn mask_hex_runs(text: &str) -> String {
    let mut masked = String::with_capacity(text.len());
    let mut run = String::new();
    for character in text.chars() {
        if character.is_ascii_hexdigit() {
            run.push(character);
            continue;
        }
        flush_hex_run(&mut masked, &mut run);
        masked.push(character);
    }
    flush_hex_run(&mut masked, &mut run);
    masked
}

fn flush_hex_run(masked: &mut String, run: &mut String) {
    if run.len() >= MIN_HEX_SECRET_LENGTH {
        masked.push_str(MASK);
    } else {
        masked.push_str(run);
    }
    run.clear();
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    fn draft(message: &str) -> ConsoleDraft {
        ConsoleDraft {
            level: ConsoleLevel::Info,
            source: ConsoleSource::App,
            module: None,
            message: message.to_owned(),
            detail: None,
        }
    }

    #[test]
    fn entries_get_increasing_ids_in_order() {
        let log = ConsoleLog::default();
        let first = log.append(draft("un")).unwrap();
        let second = log.append(draft("deux")).unwrap();
        assert!(second.id > first.id);
        let messages: Vec<_> = log
            .entries()
            .unwrap()
            .into_iter()
            .map(|entry| entry.message)
            .collect();
        assert_eq!(messages, ["un", "deux"]);
    }

    #[test]
    fn oldest_entries_are_dropped_past_capacity() {
        let log = ConsoleLog::default();
        for index in 0..CONSOLE_CAPACITY + 3 {
            log.append(draft(&format!("n°{index}"))).unwrap();
        }
        let entries = log.entries().unwrap();
        assert_eq!(entries.len(), CONSOLE_CAPACITY);
        assert_eq!(entries[0].message, "n°3");
        assert_eq!(
            entries.last().unwrap().message,
            format!("n°{}", CONSOLE_CAPACITY + 2)
        );
    }

    #[test]
    fn ids_keep_growing_after_clear() {
        let log = ConsoleLog::default();
        let before = log.append(draft("avant")).unwrap();
        log.clear().unwrap();
        assert!(log.entries().unwrap().is_empty());
        let after = log.append(draft("après")).unwrap();
        assert!(after.id > before.id);
    }

    #[test]
    fn remembered_token_is_masked_in_message_detail_and_module() {
        let log = ConsoleLog::default();
        log.remember_secret("s3cr3t-jeton").unwrap();
        let entry = log
            .append(ConsoleDraft {
                module: Some("s3cr3t-jeton".to_owned()),
                detail: Some("jeton s3cr3t-jeton refusé".to_owned()),
                ..draft("clé s3cr3t-jeton")
            })
            .unwrap();
        let json = serde_json::to_string(&entry).unwrap();
        assert!(!json.contains("s3cr3t-jeton"));
        assert_eq!(entry.message, format!("clé {MASK}"));
    }

    #[test]
    fn long_hexadecimal_strings_are_masked() {
        let token = "a".repeat(MIN_HEX_SECRET_LENGTH);
        assert_eq!(
            mask_secrets(&format!("jeton {token}."), &[]),
            format!("jeton {MASK}.")
        );
        let short = "deadbeef";
        assert_eq!(mask_secrets(short, &[]), short);
        let uuid = "123e4567-e89b-12d3-a456-426614174000";
        assert_eq!(mask_secrets(uuid, &[]), uuid);
    }

    #[test]
    fn token_assignments_are_masked() {
        assert_eq!(
            mask_secrets("ws://127.0.0.1:51717/?token=abc&x=1", &[]),
            format!("ws://127.0.0.1:51717/?token={MASK}&x=1")
        );
        assert_eq!(
            mask_secrets(r#"{"refresh_token": "xyz", "a": 1}"#, &[]),
            format!(r#"{{"refresh_token": "{MASK}", "a": 1}}"#)
        );
        assert_eq!(mask_secrets("Token: zz9", &[]), format!("Token: {MASK}"));
    }

    #[test]
    fn authorization_headers_are_masked_to_the_end_of_line() {
        assert_eq!(
            mask_secrets("Authorization: Bearer abc.def\nsuite", &[]),
            format!("Authorization: {MASK}\nsuite")
        );
    }

    #[test]
    fn ordinary_text_is_left_alone() {
        let text =
            "Plan « Façade 2 » : 12 tokens restants, max_tokens limité. Aucune autorisation.";
        assert_eq!(mask_secrets(text, &[]), text);
    }

    #[test]
    fn long_messages_are_truncated_on_a_character_boundary() {
        let log = ConsoleLog::default();
        let entry = log
            .append(draft(&"é".repeat(MAX_MESSAGE_CHARS + 5)))
            .unwrap();
        assert_eq!(entry.message.chars().count(), MAX_MESSAGE_CHARS + 1);
        assert!(entry.message.ends_with(TRUNCATION_MARK));
    }

    #[test]
    fn drafts_are_validated_on_reception() {
        let parsed: ConsoleDraft = serde_json::from_str(
            r#"{"level":"warning","source":"engine","module":"dwg-parts","message":"m"}"#,
        )
        .unwrap();
        assert_eq!(parsed.level, ConsoleLevel::Warning);
        assert_eq!(parsed.module.as_deref(), Some("dwg-parts"));
        assert!(serde_json::from_str::<ConsoleDraft>(
            r#"{"level":"fatal","source":"engine","message":"m"}"#
        )
        .is_err());
        assert!(serde_json::from_str::<ConsoleDraft>(
            r#"{"level":"info","source":"engine","message":"m","id":3}"#
        )
        .is_err());
    }

    #[test]
    fn entries_serialize_in_camel_case_without_empty_fields() {
        let log = ConsoleLog::default();
        let entry = log.append(draft("m")).unwrap();
        let json = serde_json::to_value(&entry).unwrap();
        assert_eq!(json["level"], "info");
        assert_eq!(json["source"], "app");
        assert!(json.get("module").is_none());
        assert!(json["timestamp"].as_u64().unwrap() > 0);
    }
}
