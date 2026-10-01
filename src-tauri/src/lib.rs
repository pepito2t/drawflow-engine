mod error;
mod paths;
mod sidecar;

use sidecar::RunningEngine;

pub fn run() {
    let result = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .manage(RunningEngine::default())
        .invoke_handler(tauri::generate_handler![
            sidecar::list_modules,
            sidecar::get_settings,
            sidecar::save_settings,
            sidecar::run_module,
            sidecar::cancel_run
        ])
        .run(tauri::generate_context!());
    if let Err(error) = result {
        eprintln!("Drawflow n'a pas pu démarrer : {error}");
        std::process::exit(1);
    }
}
