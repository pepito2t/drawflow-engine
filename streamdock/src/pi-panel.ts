import type { ConnectionState } from "./drawflow-client";
import { isRecord } from "./guards";
import { translate, type Language, type MessageKey } from "./i18n";

/** Keys that pick something in Drawflow; the other keys only show the connection fields. */
export interface ChoiceConfig {
  setting: string;
  source: string;
  label: MessageKey;
  placeholder: MessageKey;
  empty: MessageKey;
}

export const CHOICE_BY_ACTION: Readonly<Record<string, ChoiceConfig>> = {
  "ch.drawflow.preset": {
    setting: "presetId",
    source: "getPresets",
    label: "pi.preset",
    placeholder: "key.preset.choose",
    empty: "pi.status.noPresets",
  },
  "ch.drawflow.open-tab": {
    setting: "moduleId",
    source: "getModules",
    label: "pi.tab",
    placeholder: "key.tab.choose",
    empty: "pi.status.noModules",
  },
};

export interface ChoiceOption {
  label: string;
  value: string;
  selected: boolean;
}

export interface Choices {
  options: ChoiceOption[];
  status: string | null;
}

export interface PanelView {
  showConnection: (port: string, token: string) => void;
  showChoices: (choices: Choices) => void;
}

export interface PanelOptions {
  language: Language;
  action: string;
  uuid: string;
  settings: Settings;
  view: PanelView;
  send: (message: Record<string, unknown>) => void;
}

type Settings = Record<string, unknown>;

export const DEFAULT_PORT = "51717";

const STATUS_BY_CONNECTION: Record<Exclude<ConnectionState, "ready">, MessageKey> = {
  offline: "pi.status.offline",
  locked: "pi.status.locked",
  refused: "pi.status.refused",
};

/** What the select shows for a plugin answer; an unknown connection counts as offline. */
export function fillChoices(
  language: Language,
  config: ChoiceConfig,
  current: unknown,
  items: unknown,
  connection: unknown,
): Choices {
  const valid = Array.isArray(items) ? items.filter(isItem) : [];
  const known = valid.some((item) => item.value === current);
  const options: ChoiceOption[] = [
    { label: translate(language, config.placeholder), value: "", selected: !known },
    ...valid.map((item) => ({ ...item, selected: item.value === current })),
  ];
  return { options, status: statusFor(language, config, valid.length, connection) };
}

function statusFor(
  language: Language,
  config: ChoiceConfig,
  count: number,
  connection: unknown,
): string | null {
  if (connection !== "ready") {
    const key = isKnownConnection(connection)
      ? STATUS_BY_CONNECTION[connection]
      : "pi.status.offline";
    return translate(language, key);
  }
  return count === 0 ? translate(language, config.empty) : null;
}

function isKnownConnection(value: unknown): value is keyof typeof STATUS_BY_CONNECTION {
  return typeof value === "string" && value in STATUS_BY_CONNECTION;
}

function isItem(value: unknown): value is { label: string; value: string } {
  return isRecord(value) && typeof value.label === "string" && typeof value.value === "string";
}

/** Reads `actionInfo` as Stream Dock gives it; malformed input leaves an action without settings. */
export function parseActionInfo(raw: string): { action: string; settings: Settings } {
  const parsed = parseJson(raw);
  const action = isRecord(parsed) && typeof parsed.action === "string" ? parsed.action : "";
  const payload = isRecord(parsed) && isRecord(parsed.payload) ? parsed.payload : {};
  return { action, settings: isRecord(payload.settings) ? payload.settings : {} };
}

/** The settings panel of one key, independent from the page that displays it. */
export class Panel {
  readonly choice: ChoiceConfig | null;
  private settings: Settings;

  constructor(private readonly options: PanelOptions) {
    this.choice = CHOICE_BY_ACTION[options.action] ?? null;
    this.settings = options.settings;
  }

  register(registerEvent: string): void {
    this.options.send({ event: registerEvent, uuid: this.options.uuid });
    this.options.send({ event: "getGlobalSettings", context: this.options.uuid });
    this.requestChoices();
  }

  onMessage(raw: string): void {
    const message = parseJson(raw);
    if (!isRecord(message)) {
      return;
    }
    const payload = isRecord(message.payload) ? message.payload : {};
    if (message.event === "didReceiveGlobalSettings") {
      const settings = isRecord(payload.settings) ? payload.settings : {};
      this.options.view.showConnection(
        typeof settings.port === "string" ? settings.port : DEFAULT_PORT,
        typeof settings.token === "string" ? settings.token : "",
      );
    } else if (message.event === "sendToPropertyInspector" && this.choice !== null) {
      const current = this.settings[this.choice.setting];
      this.options.view.showChoices(
        fillChoices(this.options.language, this.choice, current, payload.items, payload.connection),
      );
    }
  }

  requestChoices(): void {
    if (this.choice !== null) {
      this.options.send({
        event: "sendToPlugin",
        action: this.options.action,
        context: this.options.uuid,
        payload: { event: this.choice.source },
      });
    }
  }

  saveChoice(value: string): void {
    if (this.choice !== null) {
      this.settings = { ...this.settings, [this.choice.setting]: value };
      this.options.send({
        event: "setSettings",
        context: this.options.uuid,
        payload: this.settings,
      });
    }
  }

  saveConnection(port: string, token: string): void {
    this.options.send({
      event: "setGlobalSettings",
      context: this.options.uuid,
      payload: { port: port.trim() || DEFAULT_PORT, token: token.trim() },
    });
  }
}

function parseJson(raw: string): unknown {
  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return null;
  }
}
