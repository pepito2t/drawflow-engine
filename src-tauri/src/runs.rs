use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, MutexGuard};
use std::time::Duration;

use tokio::sync::watch;
use tokio::time::Instant;

use crate::error::BridgeError;

pub type RunId = String;

pub trait Killable {
    fn kill_process(self) -> Result<(), BridgeError>;
}

/// A process that can be asked to stop by itself before being killed.
pub trait Stoppable: Killable {
    fn request_stop(&mut self) -> Result<(), BridgeError>;
}

/// Never sent to: it only closes, when its sender is dropped with the finished run.
type FinishedSignal = watch::Receiver<()>;

struct RunningProcess<C> {
    module_id: String,
    child: C,
    finished: watch::Sender<()>,
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

impl<C: Stoppable> RunRegistry<C> {
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
        let (finished, _) = watch::channel(());
        let process = RunningProcess {
            module_id: module_id.to_owned(),
            child,
            finished,
        };
        running.insert(run_id.clone(), process);
        Ok((run_id, handle))
    }

    /// Called once the process has terminated; wakes any cancellation waiting for it.
    pub fn finish(&self, run_id: &str) -> Result<(), BridgeError> {
        self.lock()?.remove(run_id);
        Ok(())
    }

    /// Asks the run to stop, then kills it only if it has not finished within `grace`.
    pub async fn cancel(&self, run_id: &str, grace: Duration) -> Result<(), BridgeError> {
        let finished = match self.lock()?.get_mut(run_id) {
            Some(process) => ask_to_stop(process),
            None => return Ok(()),
        };
        let deadline = Instant::now() + grace;
        if let Some(finished) = finished {
            if wait_until_finished(finished, deadline).await {
                return Ok(());
            }
        }
        match self.lock()?.remove(run_id) {
            Some(process) => process.child.kill_process(),
            None => Ok(()),
        }
    }

    /// Same as `cancel` for every run, with a single deadline shared by all of them.
    pub async fn cancel_all(&self, grace: Duration) -> Vec<BridgeError> {
        let pending: Vec<FinishedSignal> = match self.lock() {
            Ok(mut running) => running.values_mut().filter_map(ask_to_stop).collect(),
            Err(error) => return vec![error],
        };
        let deadline = Instant::now() + grace;
        for finished in pending {
            wait_until_finished(finished, deadline).await;
        }
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

/// `None` when the request cannot even be written (stdin already closed): no point waiting.
fn ask_to_stop<C: Stoppable>(process: &mut RunningProcess<C>) -> Option<FinishedSignal> {
    let finished = process.finished.subscribe();
    match process.child.request_stop() {
        Ok(()) => Some(finished),
        Err(error) => {
            eprintln!("Demande d'arrêt non transmise, arrêt forcé : {error}");
            None
        }
    }
}

async fn wait_until_finished(mut finished: FinishedSignal, deadline: Instant) -> bool {
    tokio::time::timeout_at(deadline, finished.changed())
        .await
        .is_ok()
}

pub type ChildId = u64;

/// Short-lived engine processes (one-shot requests), kept only so they can be killed at exit
/// or when they overrun their deadline.
pub struct ChildRegistry<C> {
    next_id: AtomicU64,
    children: Mutex<HashMap<ChildId, C>>,
}

impl<C> Default for ChildRegistry<C> {
    fn default() -> Self {
        Self {
            next_id: AtomicU64::new(1),
            children: Mutex::new(HashMap::new()),
        }
    }
}

impl<C: Killable> ChildRegistry<C> {
    pub fn register(&self, child: C) -> Result<ChildId, BridgeError> {
        let id = self.next_id.fetch_add(1, Ordering::Relaxed);
        self.lock()?.insert(id, child);
        Ok(id)
    }

    pub fn take(&self, id: ChildId) -> Result<Option<C>, BridgeError> {
        Ok(self.lock()?.remove(&id))
    }

    pub fn kill(&self, id: ChildId) -> Result<(), BridgeError> {
        match self.take(id)? {
            Some(child) => child.kill_process(),
            None => Ok(()),
        }
    }

    pub fn kill_all(&self) -> Vec<BridgeError> {
        let drained: Vec<C> = match self.lock() {
            Ok(mut children) => children.drain().map(|(_, child)| child).collect(),
            Err(error) => return vec![error],
        };
        drained
            .into_iter()
            .filter_map(|child| child.kill_process().err())
            .collect()
    }

    fn lock(&self) -> Result<MutexGuard<'_, HashMap<ChildId, C>>, BridgeError> {
        self.children.lock().map_err(|_| BridgeError::StatePoisoned)
    }
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;
    use std::sync::Arc;
    use tokio::sync::Notify;

    const SHORT_GRACE: Duration = Duration::from_millis(50);
    const LONG_GRACE: Duration = Duration::from_secs(5);

    #[derive(Clone, Default)]
    struct FakeChild {
        kills: Arc<Mutex<Vec<String>>>,
        name: String,
        stop_requested: Arc<Notify>,
        refuses_stop: bool,
    }

    impl Killable for FakeChild {
        fn kill_process(self) -> Result<(), BridgeError> {
            self.kills.lock().unwrap().push(self.name);
            Ok(())
        }
    }

    impl Stoppable for FakeChild {
        fn request_stop(&mut self) -> Result<(), BridgeError> {
            if self.refuses_stop {
                return Err(BridgeError::StatePoisoned);
            }
            self.stop_requested.notify_one();
            Ok(())
        }
    }

    fn child(kills: &Arc<Mutex<Vec<String>>>, name: &str) -> FakeChild {
        FakeChild {
            kills: Arc::clone(kills),
            name: name.to_owned(),
            ..FakeChild::default()
        }
    }

    /// Plays the relay task: the run finishes as soon as it is asked to stop.
    fn finishes_when_asked(
        registry: &Arc<RunRegistry<FakeChild>>,
        run_id: &str,
        child: &FakeChild,
    ) {
        let registry = Arc::clone(registry);
        let run_id = run_id.to_owned();
        let stop_requested = Arc::clone(&child.stop_requested);
        tokio::spawn(async move {
            stop_requested.notified().await;
            registry.finish(&run_id).unwrap();
        });
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

    #[tokio::test]
    async fn cancel_only_kills_the_targeted_run() {
        let registry = RunRegistry::default();
        let kills: Arc<Mutex<Vec<String>>> = Arc::default();
        let (first, _) = registry
            .start("a", || Ok(((), child(&kills, "first"))))
            .unwrap();
        registry
            .start("b", || Ok(((), child(&kills, "second"))))
            .unwrap();
        registry.cancel(&first, SHORT_GRACE).await.unwrap();
        assert_eq!(*kills.lock().unwrap(), ["first"]);
    }

    #[tokio::test]
    async fn run_stopping_in_time_is_not_killed() {
        let registry = Arc::new(RunRegistry::default());
        let kills: Arc<Mutex<Vec<String>>> = Arc::default();
        let polite = child(&kills, "polite");
        let (run_id, _) = registry.start("a", || Ok(((), polite.clone()))).unwrap();
        finishes_when_asked(&registry, &run_id, &polite);

        registry.cancel(&run_id, LONG_GRACE).await.unwrap();

        assert!(kills.lock().unwrap().is_empty());
        assert!(registry.start("a", || Ok(((), polite.clone()))).is_ok());
    }

    #[tokio::test]
    async fn run_overrunning_the_grace_period_is_killed() {
        let registry = RunRegistry::default();
        let kills: Arc<Mutex<Vec<String>>> = Arc::default();
        let (run_id, _) = registry
            .start("a", || Ok(((), child(&kills, "stuck"))))
            .unwrap();

        registry.cancel(&run_id, SHORT_GRACE).await.unwrap();

        assert_eq!(*kills.lock().unwrap(), ["stuck"]);
    }

    #[tokio::test]
    async fn run_that_cannot_be_asked_is_killed_without_waiting() {
        let registry = RunRegistry::default();
        let kills: Arc<Mutex<Vec<String>>> = Arc::default();
        let deaf = FakeChild {
            refuses_stop: true,
            ..child(&kills, "deaf")
        };
        let (run_id, _) = registry.start("a", || Ok(((), deaf))).unwrap();
        let started = Instant::now();

        registry.cancel(&run_id, LONG_GRACE).await.unwrap();

        assert!(started.elapsed() < LONG_GRACE);
        assert_eq!(*kills.lock().unwrap(), ["deaf"]);
    }

    #[test]
    fn one_shot_children_are_killed_at_exit_unless_already_finished() {
        let registry = ChildRegistry::default();
        let kills: Arc<Mutex<Vec<String>>> = Arc::default();
        let finished = registry.register(child(&kills, "finished")).unwrap();
        registry.register(child(&kills, "running")).unwrap();
        assert!(registry.take(finished).unwrap().is_some());
        assert!(registry.take(finished).unwrap().is_none());
        assert!(registry.kill_all().is_empty());
        assert_eq!(*kills.lock().unwrap(), ["running"]);
    }

    #[test]
    fn overrunning_child_is_killed_once() {
        let registry = ChildRegistry::default();
        let kills: Arc<Mutex<Vec<String>>> = Arc::default();
        let id = registry.register(child(&kills, "slow")).unwrap();
        registry.kill(id).unwrap();
        registry.kill(id).unwrap();
        assert_eq!(*kills.lock().unwrap(), ["slow"]);
    }

    #[tokio::test]
    async fn cancel_all_kills_every_run_still_running_at_the_deadline() {
        let registry = RunRegistry::default();
        let kills: Arc<Mutex<Vec<String>>> = Arc::default();
        registry
            .start("a", || Ok(((), child(&kills, "first"))))
            .unwrap();
        registry
            .start("b", || Ok(((), child(&kills, "second"))))
            .unwrap();
        assert!(registry.cancel_all(SHORT_GRACE).await.is_empty());
        let mut killed = kills.lock().unwrap().clone();
        killed.sort();
        assert_eq!(killed, ["first", "second"]);
    }

    #[tokio::test]
    async fn cancel_all_spares_the_runs_that_stop_in_time() {
        let registry = Arc::new(RunRegistry::default());
        let kills: Arc<Mutex<Vec<String>>> = Arc::default();
        let polite = child(&kills, "polite");
        let (polite_id, _) = registry.start("a", || Ok(((), polite.clone()))).unwrap();
        finishes_when_asked(&registry, &polite_id, &polite);
        registry
            .start("b", || Ok(((), child(&kills, "stuck"))))
            .unwrap();

        assert!(registry.cancel_all(SHORT_GRACE * 4).await.is_empty());

        assert_eq!(*kills.lock().unwrap(), ["stuck"]);
    }
}
