mod error;
mod paths;
mod runs;
mod sidecar;

use sidecar::EngineRuns;
use tauri::{Manager, RunEvent};

pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .manage(EngineRuns::default())
        .invoke_handler(tauri::generate_handler![
            sidecar::list_modules,
            sidecar::get_settings,
            sidecar::save_settings,
            sidecar::run_module,
            sidecar::cancel_run
        ])
        .build(tauri::generate_context!());
    match app {
        Ok(app) => app.run(|handle, event| {
            if let RunEvent::Exit = event {
                stop_engine_processes(handle);
            }
        }),
        Err(error) => {
            eprintln!("Drawflow n'a pas pu démarrer : {error}");
            std::process::exit(1);
        }
    }
}

fn stop_engine_processes(handle: &tauri::AppHandle) {
    for error in handle.state::<EngineRuns>().cancel_all() {
        eprintln!("Arrêt d'un traitement impossible : {error}");
    }
}
