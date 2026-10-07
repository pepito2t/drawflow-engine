use serde::{Serialize, Serializer};
use serde_json::{json, Value};

/// Every variant has a stable `code` the UI translates; the English `#[error]` text only feeds
/// logs and clients that do not know the code yet.
#[derive(Debug, thiserror::Error)]
pub enum BridgeError {
    #[error("Cannot start the engine: {0}")]
    Shell(#[from] tauri_plugin_shell::Error),
    #[error("Cannot prepare the parameters: {0}")]
    InputFile(#[from] std::io::Error),
    #[error("The engine did not answer within {0} s; it was stopped.")]
    EngineTimeout(u64),
    #[error("Cannot read or write the access code file: {0}")]
    AccessFile(std::io::Error),
    #[error("Cannot create the logs folder: {0}")]
    LogsFolder(std::io::Error),
    #[error("Cannot save the automations: {0}")]
    AutomationsFile(std::io::Error),
    #[error("Cannot save the local API settings: {0}")]
    IntegrationsFile(std::io::Error),
    #[error("The file {0} is unreadable: fix or delete it in the configuration folder.")]
    ConfigCorrupted(String),
    #[error("Parameters cannot be serialized: {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("Application error: {0}. Restart Drawflow if the problem persists.")]
    Tauri(#[from] tauri::Error),
    #[error("This feature is already running.")]
    RunInProgress,
    #[error("“{0}” is not a valid model name.")]
    InvalidModelName(String),
    #[error("“{0}” is not a valid feature identifier.")]
    InvalidModuleId(String),
    #[error("This address is not an allowed download page.")]
    PageNotAllowed,
    #[error("The assistant is already answering a question.")]
    AssistantBusy,
    #[error("Internal application state unavailable. Restart Drawflow.")]
    StatePoisoned,
    #[error("Port {port} cannot be used: choose a port between {min} and {max}.", max = u16::MAX)]
    InvalidPort { port: u16, min: u16 },
    #[error("Port {port} is unavailable: {detail}. Choose another port.")]
    PortUnavailable { port: u16, detail: String },
    #[error("The application is locked. Enter the access code.")]
    Locked,
    #[error("Wrong access code.")]
    WrongAccessCode,
    #[error("Every automation needs a preset.")]
    AutomationWithoutPreset,
    #[error("The folder “{0}” does not exist.")]
    AutomationFolderMissing(String),
    #[error("Cannot watch “{folder}”: {detail}")]
    AutomationWatchFailed { folder: String, detail: String },
    #[error("Too many attempts. Try again in {0} s.")]
    TooManyAttempts(u64),
    #[error("The code must contain digits only, between {min} and {max}.")]
    InvalidAccessCode { min: usize, max: usize },
    #[error("The access code file is unreadable. Delete access-code.json in the configuration folder to go back to code 0000.")]
    AccessFileCorrupted,
    #[error("Cannot save the access code.")]
    AccessHashing,
    #[error("Cannot generate a token for the local API: {0}")]
    TokenGeneration(getrandom::Error),
    #[error("The produced file cannot be found: {0}")]
    OutputMissing(String),
    #[error("This file was not produced by Drawflow: {0}")]
    OutputNotAllowed(String),
    #[error("Cannot open the file: {0}")]
    Opener(#[from] tauri_plugin_opener::Error),
}

impl BridgeError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::Shell(_) => "engineLaunch",
            Self::InputFile(_) => "inputFile",
            Self::EngineTimeout(_) => "engineTimeout",
            Self::AccessFile(_) => "accessFile",
            Self::LogsFolder(_) => "logsFolder",
            Self::AutomationsFile(_) => "automationsFile",
            Self::IntegrationsFile(_) => "integrationsFile",
            Self::ConfigCorrupted(_) => "configCorrupted",
            Self::Serialization(_) => "serialization",
            Self::Tauri(_) => "appError",
            Self::RunInProgress => "runInProgress",
            Self::InvalidModelName(_) => "invalidModelName",
            Self::InvalidModuleId(_) => "invalidModuleId",
            Self::PageNotAllowed => "pageNotAllowed",
            Self::AssistantBusy => "assistantBusy",
            Self::StatePoisoned => "statePoisoned",
            Self::InvalidPort { .. } => "invalidPort",
            Self::PortUnavailable { .. } => "portUnavailable",
            Self::Locked => "locked",
            Self::WrongAccessCode => "wrongAccessCode",
            Self::AutomationWithoutPreset => "automationWithoutPreset",
            Self::AutomationFolderMissing(_) => "automationFolderMissing",
            Self::AutomationWatchFailed { .. } => "automationWatchFailed",
            Self::TooManyAttempts(_) => "tooManyAttempts",
            Self::InvalidAccessCode { .. } => "invalidAccessCode",
            Self::AccessFileCorrupted => "accessFileCorrupted",
            Self::AccessHashing => "accessHashing",
            Self::TokenGeneration(_) => "tokenGeneration",
            Self::OutputMissing(_) => "outputMissing",
            Self::OutputNotAllowed(_) => "outputNotAllowed",
            Self::Opener(_) => "openFailed",
        }
    }

    pub fn params(&self) -> Value {
        match self {
            Self::Shell(error) => detail(error),
            Self::InputFile(error)
            | Self::AccessFile(error)
            | Self::LogsFolder(error)
            | Self::AutomationsFile(error)
            | Self::IntegrationsFile(error) => detail(error),
            Self::Serialization(error) => detail(error),
            Self::Tauri(error) => detail(error),
            Self::TokenGeneration(error) => detail(error),
            Self::Opener(error) => detail(error),
            Self::EngineTimeout(seconds) | Self::TooManyAttempts(seconds) => {
                json!({ "seconds": seconds })
            }
            Self::ConfigCorrupted(file) => json!({ "file": file }),
            Self::InvalidModelName(name) => json!({ "name": name }),
            Self::InvalidModuleId(id) => json!({ "id": id }),
            Self::InvalidPort { port, min } => json!({ "port": port, "min": min, "max": u16::MAX }),
            Self::PortUnavailable { port, detail } => json!({ "port": port, "detail": detail }),
            Self::AutomationFolderMissing(folder) => json!({ "folder": folder }),
            Self::AutomationWatchFailed { folder, detail } => {
                json!({ "folder": folder, "detail": detail })
            }
            Self::InvalidAccessCode { min, max } => json!({ "min": min, "max": max }),
            Self::OutputMissing(path) | Self::OutputNotAllowed(path) => json!({ "path": path }),
            Self::RunInProgress
            | Self::PageNotAllowed
            | Self::AssistantBusy
            | Self::StatePoisoned
            | Self::Locked
            | Self::WrongAccessCode
            | Self::AutomationWithoutPreset
            | Self::AccessFileCorrupted
            | Self::AccessHashing => json!({}),
        }
    }
}

fn detail(error: &impl std::fmt::Display) -> Value {
    json!({ "detail": error.to_string() })
}

/// The shape every bridge error takes once it leaves Rust (Tauri commands, status reports).
#[derive(Clone, Debug, Serialize, PartialEq)]
pub struct ErrorPayload {
    pub code: &'static str,
    pub params: Value,
    pub message: String,
}

impl From<&BridgeError> for ErrorPayload {
    fn from(error: &BridgeError) -> Self {
        Self {
            code: error.code(),
            params: error.params(),
            message: error.to_string(),
        }
    }
}

impl Serialize for BridgeError {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        ErrorPayload::from(self).serialize(serializer)
    }
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    fn serialized(error: BridgeError) -> Value {
        serde_json::to_value(error).unwrap()
    }

    #[test]
    fn serializes_code_params_and_english_message() {
        assert_eq!(
            serialized(BridgeError::EngineTimeout(30)),
            json!({
                "code": "engineTimeout",
                "params": { "seconds": 30 },
                "message": "The engine did not answer within 30 s; it was stopped."
            })
        );
    }

    #[test]
    fn variants_without_data_have_empty_params() {
        assert_eq!(
            serialized(BridgeError::Locked),
            json!({
                "code": "locked",
                "params": {},
                "message": "The application is locked. Enter the access code."
            })
        );
    }

    #[test]
    fn port_errors_carry_the_allowed_range() {
        let error = serialized(BridgeError::InvalidPort {
            port: 80,
            min: 1024,
        });
        assert_eq!(error["code"], "invalidPort");
        assert_eq!(
            error["params"],
            json!({ "port": 80, "min": 1024, "max": 65535 })
        );
        assert_eq!(
            error["message"],
            "Port 80 cannot be used: choose a port between 1024 and 65535."
        );
    }

    #[test]
    fn io_errors_expose_their_detail() {
        let error = serialized(BridgeError::AutomationsFile(std::io::Error::other(
            "disk full",
        )));
        assert_eq!(error["code"], "automationsFile");
        assert_eq!(error["params"], json!({ "detail": "disk full" }));
    }

    #[test]
    fn named_parameters_match_the_variant() {
        assert_eq!(
            serialized(BridgeError::InvalidAccessCode { min: 4, max: 12 })["params"],
            json!({ "min": 4, "max": 12 })
        );
        assert_eq!(
            serialized(BridgeError::TooManyAttempts(9))["params"],
            json!({ "seconds": 9 })
        );
        assert_eq!(
            serialized(BridgeError::OutputMissing("C:\\Sortie\\é.xlsx".to_owned()))["params"],
            json!({ "path": "C:\\Sortie\\é.xlsx" })
        );
        assert_eq!(
            serialized(BridgeError::ConfigCorrupted("automations.json".to_owned()))["params"],
            json!({ "file": "automations.json" })
        );
        assert_eq!(
            serialized(BridgeError::AutomationFolderMissing("D:\\Plans".to_owned()))["params"],
            json!({ "folder": "D:\\Plans" })
        );
    }
}
