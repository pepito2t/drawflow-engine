import { Suspense, use, useEffect, useState } from "react";
import { useCommands } from "../hooks/command-registry";
import { useNotificationCenter } from "../hooks/notification-center";
import { usePresets } from "../hooks/presets-context";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import type { CatalogModule } from "../lib/catalog";
import { COMMANDS } from "../lib/commands";
import { toReadableError } from "../lib/error-message";
import type { HistoryEntry } from "../lib/history";
import { listHistory, removeHistoryEntry } from "../lib/tauri/history";
import { openOutput } from "../lib/tauri/window";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { HistoryRow } from "./HistoryPanel";
import { Loader } from "./Spinner";

const RECENT_RUNS = 5;

interface TodayPanelProps {
  modules: CatalogModule[];
}

/** The first screen: what needs attention, what was just done, what can run in one click. */
export function TodayPanel({ modules }: TodayPanelProps) {
  const { id, promise, retry } = useRetryablePromise(listHistory);
  const { subscribe } = useNotificationCenter();
  const [missingSetup, setMissingSetup] = useState(0);
  useEffect(
    () =>
      subscribe((event) => {
        if (event.type === "runFinished") retry();
        if (event.type === "setupNeeded") setMissingSetup(event.missing);
      }),
    [subscribe, retry],
  );

  return (
    <section className="module-workspace today">
      <header>
        <h1>Aujourd'hui</h1>
        <p>Ce qui vous attend, ce qui vient d'être fait, ce qui se lance en un clic.</p>
      </header>
      {missingSetup > 0 && <SetupReminder missing={missingSetup} />}
      <PresetsBlock modules={modules} />
      <ErrorBoundary
        key={id}
        fallback={(error) => (
          <ErrorPanel title="Historique indisponible" message={toReadableError(error).message} />
        )}
      >
        <Suspense fallback={<Loader label="Derniers traitements…" />}>
          <RecentRuns entriesPromise={promise} onChanged={retry} />
        </Suspense>
      </ErrorBoundary>
    </section>
  );
}

function SetupReminder({ missing }: { missing: number }) {
  const { execute } = useCommands();
  return (
    <div className="today-block today-setup">
      <strong>
        {String(missing)} élément{missing > 1 ? "s" : ""} à installer ou à configurer
      </strong>
      <button
        type="button"
        className="primary"
        onClick={() => {
          execute(COMMANDS.openSetup, {}).catch(console.error);
        }}
      >
        Configurer
      </button>
    </div>
  );
}

function PresetsBlock({ modules }: { modules: CatalogModule[] }) {
  const { presets } = usePresets();
  const { execute } = useCommands();
  const [error, setError] = useState<string | null>(null);
  const moduleName = (moduleId: string) =>
    modules.find((module) => module.manifest.id === moduleId)?.manifest.name ?? moduleId;
  const run = (presetId: string) => {
    execute(COMMANDS.runPreset, { presetId })
      .then((result) => {
        if (!result.ok) setError(result.error);
      })
      .catch((failure: unknown) => {
        setError(toReadableError(failure).message);
      });
  };
  return (
    <div className="today-block">
      <h2>Lancer en un clic</h2>
      {presets.length === 0 ? (
        <p className="muted">
          Aucun préréglage. Dans une fonctionnalité, remplissez le formulaire puis « Enregistrer
          comme préréglage ».
        </p>
      ) : (
        <ul className="today-presets">
          {presets.map((preset) => (
            <li key={preset.id}>
              <span>
                <strong>{preset.name}</strong>
                <span className="muted"> · {moduleName(preset.module)}</span>
              </span>
              <button
                type="button"
                className="primary"
                onClick={() => {
                  run(preset.id);
                }}
              >
                Lancer
              </button>
            </li>
          ))}
        </ul>
      )}
      {error && <ErrorPanel title="Lancement impossible" message={error} />}
    </div>
  );
}

function RecentRuns({
  entriesPromise,
  onChanged,
}: {
  entriesPromise: Promise<HistoryEntry[]>;
  onChanged: () => void;
}) {
  const entries = use(entriesPromise).slice(0, RECENT_RUNS);
  const { execute } = useCommands();
  const [error, setError] = useState<string | null>(null);
  const fail = (failure: unknown) => {
    setError(toReadableError(failure).message);
  };
  return (
    <div className="today-block">
      <div className="today-block-header">
        <h2>Derniers traitements</h2>
        <button
          type="button"
          className="link-button"
          onClick={() => {
            execute(COMMANDS.openHistory, {}).catch(console.error);
          }}
        >
          Tout l'historique
        </button>
      </div>
      {entries.length === 0 ? (
        <p className="muted">
          Rien encore aujourd'hui. Lancez une fonctionnalité ou un préréglage.
        </p>
      ) : (
        <ul className="history-list">
          {entries.map((entry) => (
            <HistoryRow
              key={entry.id}
              entry={entry}
              onOpen={(path) => {
                openOutput(path).catch(fail);
              }}
              onRerun={(target) => {
                execute(COMMANDS.runFeature, { moduleId: target.module, inputs: target.inputs })
                  .then((result) => {
                    if (!result.ok) setError(result.error);
                  })
                  .catch(fail);
              }}
              onRemove={(target) => {
                removeHistoryEntry(target.id).then(onChanged).catch(fail);
              }}
            />
          ))}
        </ul>
      )}
      {error && <ErrorPanel title="Action impossible" message={error} />}
    </div>
  );
}
