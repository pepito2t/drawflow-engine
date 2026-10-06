mod access;
mod assistant;
mod automations;
mod error;
mod integrations;
mod outputs;
mod paths;
mod runs;
mod setup;
mod sidecar;
mod updates;

use access::AccessLock;
use assistant::AssistantTurn;
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
        .manage(AssistantTurn::default())
        .manage(IntegrationState::default())
        .manage(automations::AutomationState::default())
        .manage(outputs::KnownOutputs::default())
        .invoke_handler(tauri::generate_handler![
            access::lock_status,
            updates::updater_configured,
            outputs::open_output,
            outputs::open_logs_folder,
            integrations::integration_status,
            integrations::integration_update,
            integrations::integration_reply,
            integrations::integration_publish,
            automations::automation_status,
            automations::automation_save,
            access::unlock,
            access::change_access_code,
            sidecar::list_modules,
            sidecar::get_settings,
            sidecar::save_settings,
            sidecar::engine_request,
            sidecar::run_module,
            sidecar::cancel_run,
            assistant::assistant_chat,
            assistant::assistant_cancel,
            setup::run_setup_action,
            setup::open_download_page,
            setup::pull_model
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
    if let Err(error) = handle.state::<AssistantTurn>().stop() {
        eprintln!("Arrêt de l'assistant impossible : {error}");
    }
}
