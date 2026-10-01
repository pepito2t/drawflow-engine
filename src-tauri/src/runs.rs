use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, MutexGuard};

use crate::error::BridgeError;

pub type RunId = String;

pub trait Killable {
    fn kill_process(self) -> Result<(), BridgeError>;
}

struct RunningProcess<C> {
    module_id: String,
    child: C,
}

/// Tracks engine processes so several features can run at once, one run per feature.
pub struct RunRegistry<C> {
    next_id: AtomicU64,
    running: Mutex<HashMap<RunId, RunningProcess<C>>>,
}

impl<C> Default for RunRegistry<C> {
    fn default() -> Self {
        Self {
            next_id: AtomicU64::new(1),
            running: Mutex::new(HashMap::new()),
        }
    }
}

impl<C: Killable> RunRegistry<C> {
    /// Spawns through `spawn` only if the module is idle, so the check and the insert are atomic.
    pub fn start<T>(
        &self,
        module_id: &str,
        spawn: impl FnOnce() -> Result<(T, C), BridgeError>,
    ) -> Result<(RunId, T), BridgeError> {
        let mut running = self.lock()?;
        if running
            .values()
            .any(|process| process.module_id == module_id)
        {
            return Err(BridgeError::RunInProgress);
        }
        let (handle, child) = spawn()?;
        let run_id = format!("run-{}", self.next_id.fetch_add(1, Ordering::Relaxed));
        let process = RunningProcess {
            module_id: module_id.to_owned(),
            child,
        };
        running.insert(run_id.clone(), process);
        Ok((run_id, handle))
    }

    pub fn finish(&self, run_id: &str) -> Result<(), BridgeError> {
        self.lock()?.remove(run_id);
        Ok(())
    }

    pub fn cancel(&self, run_id: &str) -> Result<(), BridgeError> {
        match self.lock()?.remove(run_id) {
            Some(process) => process.child.kill_process(),
            None => Ok(()),
        }
    }

    pub fn cancel_all(&self) -> Vec<BridgeError> {
        let drained: Vec<RunningProcess<C>> = match self.lock() {
            Ok(mut running) => running.drain().map(|(_, process)| process).collect(),
            Err(error) => return vec![error],
        };
        drained
            .into_iter()
            .filter_map(|process| process.child.kill_process().err())
            .collect()
    }

    fn lock(&self) -> Result<MutexGuard<'_, HashMap<RunId, RunningProcess<C>>>, BridgeError> {
        self.running.lock().map_err(|_| BridgeError::StatePoisoned)
    }
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;
    use std::sync::Arc;

    #[derive(Clone, Default)]
    struct FakeChild {
        kills: Arc<Mutex<Vec<String>>>,
        name: String,
    }

    impl Killable for FakeChild {
        fn kill_process(self) -> Result<(), BridgeError> {
            self.kills.lock().unwrap().push(self.name);
            Ok(())
        }
    }

    fn child(kills: &Arc<Mutex<Vec<String>>>, name: &str) -> FakeChild {
        FakeChild {
            kills: Arc::clone(kills),
            name: name.to_owned(),
        }
    }

    #[test]
    fn different_modules_run_concurrently_with_distinct_ids() {
        let registry = RunRegistry::default();
        let kills = Arc::default();
        let (first, _) = registry
            .start("dwg-parts", || Ok(((), child(&kills, "a"))))
            .unwrap();
        let (second, _) = registry
            .start("pdf-report", || Ok(((), child(&kills, "b"))))
            .unwrap();
        assert_ne!(first, second);
    }

    #[test]
    fn same_module_cannot_run_twice_and_does_not_spawn() {
        let registry = RunRegistry::default();
        let kills = Arc::default();
        registry
            .start("dwg-parts", || Ok(((), child(&kills, "a"))))
            .unwrap();
        let mut spawned = false;
        let result = registry.start("dwg-parts", || {
            spawned = true;
            Ok(((), child(&kills, "b")))
        });
        assert!(matches!(result, Err(BridgeError::RunInProgress)));
        assert!(!spawned);
    }

    #[test]
    fn finished_module_can_run_again() {
        let registry = RunRegistry::default();
        let kills = Arc::default();
        let (run_id, _) = registry
            .start("hello", || Ok(((), child(&kills, "a"))))
            .unwrap();
        registry.finish(&run_id).unwrap();
        assert!(registry
            .start("hello", || Ok(((), child(&kills, "b"))))
            .is_ok());
    }

    #[test]
    fn cancel_only_kills_the_targeted_run() {
        let registry = RunRegistry::default();
        let kills: Arc<Mutex<Vec<String>>> = Arc::default();
        let (first, _) = registry
            .start("a", || Ok(((), child(&kills, "first"))))
            .unwrap();
        registry
            .start("b", || Ok(((), child(&kills, "second"))))
            .unwrap();
        registry.cancel(&first).unwrap();
        assert_eq!(*kills.lock().unwrap(), ["first"]);
    }

    #[test]
    fn cancel_all_kills_every_run() {
        let registry = RunRegistry::default();
        let kills: Arc<Mutex<Vec<String>>> = Arc::default();
        registry
            .start("a", || Ok(((), child(&kills, "first"))))
            .unwrap();
        registry
            .start("b", || Ok(((), child(&kills, "second"))))
            .unwrap();
        assert!(registry.cancel_all().is_empty());
        let mut killed = kills.lock().unwrap().clone();
        killed.sort();
        assert_eq!(killed, ["first", "second"]);
    }
}
