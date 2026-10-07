use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::thread::sleep;
use std::time::Duration;

use tauri::{AppHandle, Manager};

use crate::error::BridgeError;

const SETTINGS_FILE_NAME: &str = "settings.json";
// Antivirus and indexers hold freshly written files for a moment on Windows.
const REPLACE_ATTEMPTS: u32 = 5;
const REPLACE_RETRY_DELAY: Duration = Duration::from_millis(40);

pub fn settings_file(app: &AppHandle) -> Result<PathBuf, BridgeError> {
    Ok(app.path().app_config_dir()?.join(SETTINGS_FILE_NAME))
}

/// Writes a uniquely named temporary file next to the target, flushes it to disk, then
/// replaces the target, so a crash or a concurrent save never leaves a half-written file.
pub fn write_atomically(path: &Path, content: &[u8]) -> std::io::Result<()> {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent)?;
    let mut temporary = tempfile::NamedTempFile::new_in(parent)?;
    temporary.write_all(content)?;
    temporary.as_file().sync_all()?;
    let mut attempt = 1;
    loop {
        match temporary.persist(path) {
            Ok(_file) => return Ok(()),
            Err(error)
                if error.error.kind() == std::io::ErrorKind::PermissionDenied
                    && attempt < REPLACE_ATTEMPTS =>
            {
                temporary = error.file;
                attempt += 1;
                sleep(REPLACE_RETRY_DELAY);
            }
            Err(error) => return Err(error.error),
        }
    }
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;

    #[test]
    fn replaces_the_target_and_leaves_no_temporary_file() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join("Réglages").join("settings.json");
        write_atomically(&path, b"{\"a\":1}").unwrap();
        write_atomically(&path, b"{\"a\":2}").unwrap();
        assert_eq!(fs::read_to_string(&path).unwrap(), "{\"a\":2}");
        let leftovers: Vec<_> = fs::read_dir(path.parent().unwrap()).unwrap().collect();
        assert_eq!(leftovers.len(), 1);
    }
}
