// Settings panel of a Drawflow key, run by the browser of Stream Dock. Stream Dock calls
// connectElgatoStreamDeckSocket (name kept from the Stream Deck SDK it is compatible with).
import { languageFromInfo, translate, type Language, type MessageKey } from "./i18n";
import { Panel, parseActionInfo, type PanelView } from "./pi-panel";

type ConnectInspector = (
  port: string,
  uuid: string,
  registerEvent: string,
  info: string,
  actionInfo: string,
) => void;

declare global {
  interface Window {
    connectElgatoStreamDeckSocket: ConnectInspector;
  }
}

function element<T extends HTMLElement>(id: string, kind: new () => T): T {
  const found = document.getElementById(id);
  if (!(found instanceof kind)) {
    throw new Error(`Élément ${id} absent de la page du panneau.`);
  }
  return found;
}

function applyTranslations(language: Language): void {
  document.documentElement.lang = language;
  for (const node of document.querySelectorAll<HTMLElement>("[data-i18n]")) {
    node.textContent = translate(language, node.dataset.i18n as MessageKey);
  }
}

function domView(): PanelView {
  const port = element("port", HTMLInputElement);
  const token = element("token", HTMLInputElement);
  const select = element("choice", HTMLSelectElement);
  const status = element("status", HTMLElement);
  return {
    showConnection: (portValue, tokenValue) => {
      port.value = portValue;
      token.value = tokenValue;
    },
    showChoices: ({ options, status: text }) => {
      select.replaceChildren(
        ...options.map((option) => new Option(option.label, option.value, false, option.selected)),
      );
      status.textContent = text ?? "";
      status.hidden = text === null;
    },
  };
}

function bindInputs(panel: Panel, language: Language): void {
  const block = element("choice-block", HTMLElement);
  const select = element("choice", HTMLSelectElement);
  const port = element("port", HTMLInputElement);
  const token = element("token", HTMLInputElement);
  block.hidden = panel.choice === null;
  if (panel.choice !== null) {
    element("choice-label", HTMLLabelElement).textContent = translate(language, panel.choice.label);
    select.addEventListener("change", () => {
      panel.saveChoice(select.value);
    });
    select.addEventListener("focus", () => {
      panel.requestChoices();
    });
  }
  const saveConnection = (): void => {
    panel.saveConnection(port.value, token.value);
  };
  port.addEventListener("change", saveConnection);
  token.addEventListener("change", saveConnection);
}

window.connectElgatoStreamDeckSocket = (port, uuid, registerEvent, info, actionInfo) => {
  const language = languageFromInfo(info);
  const { action, settings } = parseActionInfo(actionInfo);
  applyTranslations(language);
  const socket = new WebSocket(`ws://127.0.0.1:${port}`);
  const panel = new Panel({
    language,
    action,
    uuid,
    settings,
    view: domView(),
    send: (message) => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
      }
    },
  });
  socket.onopen = () => {
    panel.register(registerEvent);
  };
  socket.onmessage = (event: MessageEvent<unknown>) => {
    panel.onMessage(String(event.data));
  };
  bindInputs(panel, language);
};
