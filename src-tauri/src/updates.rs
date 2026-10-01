use tauri::{App, AppHandle};

const UPDATER_PLUGIN: &str = "updater";

/// The updater key and endpoint are injected only in release builds (see release.yml);
/// development builds simply run without automatic updates.
pub fn register_updater(app: &mut App) -> Result<(), Box<dyn std::error::Error>> {
    if is_configured(app.handle()) {
        app.handle()
            .plugin(tauri_plugin_updater::Builder::new().build())?;
    }
    Ok(())
}

#[tauri::command]
pub fn updater_configured(app: AppHandle) -> bool {
    is_configured(&app)
}

fn is_configured(app: &AppHandle) -> bool {
    app.config().plugins.0.contains_key(UPDATER_PLUGIN)
}
