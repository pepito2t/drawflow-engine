mod access;
mod assistant;
mod automations;
mod bounded_set;
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
use sidecar::{EngineRuns, OneShotChildren};
use std::time::Duration;

use tauri::{Manager, RunEvent};

/// Quitting must stay quick: whatever has not stopped by then is killed.
const EXIT_STOP_TIMEOUT: Duration = Duration::from_secs(2);

pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_opener::init())
        .setup(updates::register_updater)
        .manage(EngineRuns::default())
        .manage(OneShotChildren::default())
        .manage(AccessLock::default())
        .manage(AssistantTurn::default())
        .manage(IntegrationState::default())
        .manage(automations::AutomationState::default())
        .manage(outputs::KnownOutputs::default())
        .invoke_handler(tauri::generate_handler![
            access::lock_status,
            updates::updater_configured,
            updates::prepare_for_update,
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

/// Single exit cleanup, shared by the normal exit and the updater's restart. Blocks the calling
/// thread, which must not be an async task.
pub(crate) fn stop_engine_processes(handle: &tauri::AppHandle) {
    let runs = handle.state::<EngineRuns>();
    for error in tauri::async_runtime::block_on(runs.cancel_all(EXIT_STOP_TIMEOUT)) {
        eprintln!("Arrêt d'un traitement impossible : {error}");
    }
    for error in handle.state::<OneShotChildren>().kill_all() {
        eprintln!("Arrêt d'une requête du moteur impossible : {error}");
    }
    if let Err(error) = handle.state::<AssistantTurn>().stop() {
        eprintln!("Arrêt de l'assistant impossible : {error}");
    }
}
