import { t } from "../i18n/shell";
import { useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { usePresets } from "../hooks/presets-context";
import { toReadableError, type ReadableError } from "../lib/error-message";
import type { FormValues } from "../lib/form-schema";
import { presetsFor, type Preset } from "../lib/presets";
import { ErrorPanel } from "./ErrorPanel";

interface PresetBarProps {
  moduleId: string;
  disabled: boolean;
  currentInputs: () => FormValues;
  onLoad: (preset: Preset) => void;
}

const NO_PRESET = "";

export function PresetBar({ moduleId, disabled, currentInputs, onLoad }: PresetBarProps) {
  const { presets, save, remove } = usePresets();
  const { publish } = useNotificationCenter();
  const [selectedId, setSelectedId] = useState(NO_PRESET);
  const [draftName, setDraftName] = useState<string | null>(null);
  const [error, setError] = useState<ReadableError | null>(null);
  const [confirmRemove, setConfirmRemove] = useState(false);
  const available = presetsFor(presets, moduleId);
  const selected = available.find((preset) => preset.id === selectedId);

  const attempt = (task: Promise<void>, onDone: () => void) => {
    setError(null);
    task.then(onDone).catch((reason: unknown) => {
      setError(toReadableError(reason));
    });
  };

  const confirmSave = () => {
    const name = draftName?.trim() ?? "";
    attempt(
      save(moduleId, name, currentInputs(), selected?.name === name ? selected.id : undefined),
      () => {
        publish({ type: "presetSaved", name });
        setDraftName(null);
      },
    );
  };

  return (
    <div className="preset-bar">
      <select
        aria-label={t("presetBar.title")}
        value={selectedId}
        disabled={disabled}
        onChange={(event) => {
          setSelectedId(event.target.value);
          setConfirmRemove(false);
          const preset = available.find((item) => item.id === event.target.value);
          if (preset) {
            onLoad(preset);
          }
        }}
      >
        <option value={NO_PRESET}>
          {available.length ? t("presetBar.load") : t("presetBar.none")}
        </option>
        {available.map((preset) => (
          <option key={preset.id} value={preset.id}>
            {preset.name}
          </option>
        ))}
      </select>
      {draftName === null ? (
        <button
          type="button"
          disabled={disabled}
          onClick={() => {
            setDraftName(selected?.name ?? "");
          }}
        >
          {t("presetBar.saveAs")}
        </button>
      ) : (
        <>
          <input
            type="text"
            aria-label={t("presetBar.name")}
            placeholder={t("presetBar.name")}
            autoFocus
            value={draftName}
            onChange={(event) => {
              setDraftName(event.target.value);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter") confirmSave();
              if (event.key === "Escape") setDraftName(null);
            }}
          />
          <button
            type="button"
            className="primary"
            disabled={!draftName.trim()}
            onClick={confirmSave}
          >
            {t("presetBar.save")}
          </button>
          <button
            type="button"
            onClick={() => {
              setDraftName(null);
            }}
          >
            {t("presetBar.cancel")}
          </button>
        </>
      )}
      {selected && draftName === null && !confirmRemove && (
        <button
          type="button"
          disabled={disabled}
          onClick={() => {
            setConfirmRemove(true);
          }}
        >
          {t("presetBar.remove")}
        </button>
      )}
      {selected && draftName === null && confirmRemove && (
        <>
          <span>{t("presetBar.confirmRemove", { name: selected.name })}</span>
          <button
            type="button"
            className="primary"
            disabled={disabled}
            onClick={() => {
              setConfirmRemove(false);
              attempt(remove(selected.id), () => {
                setSelectedId(NO_PRESET);
              });
            }}
          >
            {t("presetBar.remove")}
          </button>
          <button
            type="button"
            onClick={() => {
              setConfirmRemove(false);
            }}
          >
            {t("presetBar.cancel")}
          </button>
        </>
      )}
      {error && (
        <ErrorPanel title={t("presetBar.saveFailed")} message={error.message} hint={error.hint} />
      )}
    </div>
  );
}
