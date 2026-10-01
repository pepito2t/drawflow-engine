use serde::{Serialize, Serializer};

#[derive(Debug, thiserror::Error)]
pub enum BridgeError {
    #[error("Impossible de lancer le moteur : {0}")]
    Shell(#[from] tauri_plugin_shell::Error),
    #[error("Impossible de préparer les paramètres : {0}")]
    InputFile(#[from] std::io::Error),
    #[error("Paramètres non sérialisables : {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("Impossible de transmettre un message à l'interface : {0}")]
    Channel(#[from] tauri::Error),
    #[error("Un traitement est déjà en cours.")]
    RunInProgress,
    #[error("État interne du moteur indisponible.")]
    StatePoisoned,
    #[error("Le moteur a échoué (code {code:?}) : {details}")]
    EngineFailed { code: Option<i32>, details: String },
}

impl Serialize for BridgeError {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(&self.to_string())
    }
}
