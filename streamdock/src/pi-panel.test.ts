import { describe, expect, it } from "vitest";
import {
  CHOICE_BY_ACTION,
  Panel,
  fillChoices,
  parseActionInfo,
  type ChoiceConfig,
  type Choices,
} from "./pi-panel";

const PRESET = CHOICE_BY_ACTION["ch.drawflow.preset"] as ChoiceConfig;
const ITEMS = [
  { label: "Tour B (Pièces)", value: "p1" },
  { label: "Façade nord (Pièces)", value: "p2" },
];

function setup(action = "ch.drawflow.preset", language: "fr" | "en" = "fr") {
  const sent: Record<string, unknown>[] = [];
  const connections: [string, string][] = [];
  const choices: Choices[] = [];
  const panel = new Panel({
    language,
    action,
    uuid: "ctx",
    settings: { presetId: "p2" },
    view: {
      showConnection: (port, token) => connections.push([port, token]),
      showChoices: (shown) => choices.push(shown),
    },
    send: (message) => sent.push(message),
  });
  return { panel, sent, connections, choices };
}

describe("fillChoices", () => {
  it("lists Drawflow's items with the current one selected", () => {
    const { options, status } = fillChoices("fr", PRESET, "p2", ITEMS, "ready");

    expect(options.map((option) => option.value)).toEqual(["", "p1", "p2"]);
    expect(options.find((option) => option.selected)?.value).toBe("p2");
    expect(options[0]?.label).toBe("Choisir un préréglage");
    expect(status).toBeNull();
  });

  it("selects the placeholder when the saved item no longer exists", () => {
    const { options } = fillChoices("fr", PRESET, "gone", ITEMS, "ready");

    expect(options.find((option) => option.selected)?.value).toBe("");
  });

  it("tells why the list is empty according to the connection", () => {
    expect(fillChoices("fr", PRESET, "", [], "ready").status).toBe(
      "Aucun préréglage enregistré dans Drawflow.",
    );
    expect(fillChoices("fr", PRESET, "", [], "offline").status).toContain("hors ligne");
    expect(fillChoices("fr", PRESET, "", [], "locked").status).toContain("verrouillée");
    expect(fillChoices("fr", PRESET, "", [], "refused").status).toContain("Jeton refusé");
    expect(fillChoices("en", PRESET, "", [], undefined).status).toBe(
      "Drawflow is offline: start Drawflow on this computer.",
    );
  });

  it("ignores malformed items", () => {
    const { options } = fillChoices("fr", PRESET, "", [{ label: 1 }, "x", ITEMS[0]], "ready");

    expect(options.map((option) => option.value)).toEqual(["", "p1"]);
  });
});

describe("parseActionInfo", () => {
  it("reads the action and its settings, or falls back to nothing", () => {
    expect(
      parseActionInfo('{"action":"ch.drawflow.preset","payload":{"settings":{"presetId":"p1"}}}'),
    ).toEqual({ action: "ch.drawflow.preset", settings: { presetId: "p1" } });
    expect(parseActionInfo("not json")).toEqual({ action: "", settings: {} });
    expect(parseActionInfo('{"action":"x"}')).toEqual({ action: "x", settings: {} });
  });
});

describe("Panel", () => {
  it("registers, asks for the global settings and for the choices", () => {
    const { panel, sent } = setup();

    panel.register("registerPropertyInspector");

    expect(sent).toEqual([
      { event: "registerPropertyInspector", uuid: "ctx" },
      { event: "getGlobalSettings", context: "ctx" },
      {
        event: "sendToPlugin",
        action: "ch.drawflow.preset",
        context: "ctx",
        payload: { event: "getPresets" },
      },
    ]);
  });

  it("has no choice to ask for on a plain command key", () => {
    const { panel, sent } = setup("ch.drawflow.cancel-all");

    panel.register("registerPropertyInspector");

    expect(panel.choice).toBeNull();
    expect(sent.map((message) => message.event)).toEqual([
      "registerPropertyInspector",
      "getGlobalSettings",
    ]);
  });

  it("shows the global settings and the choices it receives", () => {
    const { panel, connections, choices } = setup();

    panel.onMessage(
      JSON.stringify({
        event: "didReceiveGlobalSettings",
        payload: { settings: { port: "51800", token: "secret" } },
      }),
    );
    panel.onMessage(JSON.stringify({ event: "didReceiveGlobalSettings", payload: {} }));
    panel.onMessage(
      JSON.stringify({
        event: "sendToPropertyInspector",
        payload: { event: "getPresets", items: ITEMS, connection: "ready" },
      }),
    );

    expect(connections).toEqual([
      ["51800", "secret"],
      ["51717", ""],
    ]);
    expect(choices[0]?.options.find((option) => option.selected)?.value).toBe("p2");
  });

  it("survives messages it cannot read", () => {
    const { panel, connections, choices } = setup();

    panel.onMessage("not json");
    panel.onMessage("42");
    panel.onMessage('{"event":"sendToPropertyInspector"}');

    expect(connections).toEqual([]);
    expect(choices).toHaveLength(1);
  });

  it("saves the chosen item with the other settings of the key", () => {
    const { panel, sent } = setup();

    panel.saveChoice("p1");

    expect(sent).toEqual([{ event: "setSettings", context: "ctx", payload: { presetId: "p1" } }]);
  });

  it("saves the connection with the default port when left empty", () => {
    const { panel, sent } = setup();

    panel.saveConnection("  ", " secret ");

    expect(sent).toEqual([
      { event: "setGlobalSettings", context: "ctx", payload: { port: "51717", token: "secret" } },
    ]);
  });
});
