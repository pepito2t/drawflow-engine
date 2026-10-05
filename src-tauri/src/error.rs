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
    #[error("« {0} » n'est pas un nom de modèle valide.")]
    InvalidModelName(String),
    #[error("« {0} » n'est pas un identifiant de fonctionnalité valide.")]
    InvalidModuleId(String),
    #[error("Cette adresse n'est pas une page de téléchargement autorisée.")]
    PageNotAllowed,
    #[error("L'assistant répond déjà à une question.")]
    AssistantBusy,
    #[error("État interne du moteur indisponible.")]
    StatePoisoned,
    #[error("L'application est verrouillée. Saisissez le code d'accès.")]
    Locked,
    #[error("Code d'accès incorrect.")]
    WrongAccessCode,
    #[error("Trop de tentatives. Réessayez dans {0} s.")]
    TooManyAttempts(u64),
    #[error("Le code doit contenir uniquement des chiffres, entre {min} et {max}.")]
    InvalidAccessCode { min: usize, max: usize },
    #[error("Le fichier du code d'accès est illisible. Supprimez access-code.json dans le dossier de configuration pour revenir au code 0000.")]
    AccessFileCorrupted,
    #[error("Impossible d'enregistrer le code d'accès.")]
    AccessHashing,
    #[error("Le fichier produit est introuvable : {0}")]
    OutputMissing(String),
    #[error("Ce fichier n'a pas été produit par Drawflow : {0}")]
    OutputNotAllowed(String),
    #[error("Impossible d'ouvrir le fichier : {0}")]
    Opener(#[from] tauri_plugin_opener::Error),
}

impl Serialize for BridgeError {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(&self.to_string())
    }
}
