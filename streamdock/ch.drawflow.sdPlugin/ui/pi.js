// Settings panel of a Drawflow key. Stream Dock calls connectElgatoStreamDeckSocket (name kept
// from the Stream Deck SDK it is compatible with) once the panel is shown.
"use strict";

const DEFAULT_PORT = "51717";
const panel = { socket: null, uuid: "", action: "", settings: {} };

function send(message) {
  if (panel.socket && panel.socket.readyState === WebSocket.OPEN) {
    panel.socket.send(JSON.stringify(message));
  }
}

function saveSettings(changes) {
  panel.settings = { ...panel.settings, ...changes };
  send({ event: "setSettings", context: panel.uuid, payload: panel.settings });
}

function saveGlobalSettings() {
  const port = document.getElementById("port").value.trim() || DEFAULT_PORT;
  const token = document.getElementById("token").value.trim();
  send({ event: "setGlobalSettings", context: panel.uuid, payload: { port, token } });
}

function fillChoices(items) {
  const select = document.getElementById("choice");
  if (!select) return;
  const setting = select.dataset.setting;
  const current = panel.settings[setting] ?? "";
  select.replaceChildren(new Option(select.dataset.placeholder, ""));
  for (const item of items) {
    select.add(new Option(item.label, item.value, false, item.value === current));
  }
  if (items.length === 0) {
    select.add(new Option("Drawflow hors ligne : lancez Drawflow sur ce poste", "", false, false));
  }
}

function onMessage(raw) {
  const message = JSON.parse(raw.data);
  if (message.event === "didReceiveGlobalSettings") {
    const settings = message.payload?.settings ?? {};
    document.getElementById("port").value = settings.port ?? DEFAULT_PORT;
    document.getElementById("token").value = settings.token ?? "";
  } else if (message.event === "sendToPropertyInspector") {
    fillChoices(message.payload?.items ?? []);
  }
}

function bindInputs() {
  const select = document.getElementById("choice");
  if (select) {
    select.addEventListener("change", () =>
      saveSettings({ [select.dataset.setting]: select.value }),
    );
    select.addEventListener("focus", () => requestChoices());
  }
  for (const id of ["port", "token"]) {
    document.getElementById(id).addEventListener("change", saveGlobalSettings);
  }
}

function requestChoices() {
  const select = document.getElementById("choice");
  if (select) {
    send({
      event: "sendToPlugin",
      action: panel.action,
      context: panel.uuid,
      payload: { event: select.dataset.source },
    });
  }
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- called by Stream Dock
function connectElgatoStreamDeckSocket(port, uuid, registerEvent, _info, actionInfo) {
  const action = JSON.parse(actionInfo);
  panel.uuid = uuid;
  panel.action = action.action;
  panel.settings = action.payload?.settings ?? {};
  panel.socket = new WebSocket(`ws://127.0.0.1:${port}`);
  panel.socket.onopen = () => {
    send({ event: registerEvent, uuid });
    send({ event: "getGlobalSettings", context: uuid });
    requestChoices();
  };
  panel.socket.onmessage = onMessage;
  bindInputs();
}
