mod access;
mod error;
mod integrations;
mod outputs;
mod paths;
mod runs;
mod sidecar;
mod updates;

use access::AccessLock;
use integrations::IntegrationState;
use sidecar::EngineRuns;
use tauri::{Manager, RunEvent};

pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_opener::init())
        .setup(updates::register_updater)
        .manage(EngineRuns::default())
        .manage(AccessLock::default())
        .manage(IntegrationState::default())
        .invoke_handler(tauri::generate_handler![
            access::lock_status,
            updates::updater_configured,
            outputs::open_output,
            integrations::integration_status,
            integrations::integration_update,
            integrations::integration_reply,
            integrations::integration_publish,
            access::unlock,
            access::change_access_code,
            sidecar::list_modules,
            sidecar::get_settings,
            sidecar::save_settings,
            sidecar::engine_request,
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
