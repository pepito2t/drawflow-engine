use serde::{Serialize, Serializer};

#[derive(Debug, thiserror::Error)]
pub enum BridgeError {
    #[error("Impossible de lancer le moteur : {0}")]
    Shell(#[from] tauri_plugin_shell::Error),
    #[error("Impossible de préparer les paramètres : {0}")]
    InputFile(#[from] std::io::Error),
    #[error("Paramètres non sérialisables : {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("Erreur de l'application : {0}")]
    Tauri(#[from] tauri::Error),
    #[error("Cette fonctionnalité est déjà en cours d'exécution.")]
    RunInProgress,
    #[error("État interne du moteur indisponible.")]
    StatePoisoned,
}

impl Serialize for BridgeError {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(&self.to_string())
    }
}
