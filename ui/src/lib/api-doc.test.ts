import { describe, expect, it } from "vitest";
import documentation from "../../../docs/api-locale.md?raw";
import eventsSource from "./app-events.ts?raw";
import { COMMAND_ARGUMENTS } from "./commands";

const EVENT_TYPE_LITERAL = /type: "([A-Za-z]+)"/g;

function declaredEventTypes(): string[] {
  return [...eventsSource.matchAll(EVENT_TYPE_LITERAL)].flatMap((match) => match[1] ?? []);
}

function documentedNames(): string[] {
  return [...documentation.matchAll(/`([a-z][A-Za-z.-]*)`/g)].flatMap((match) => match[1] ?? []);
}

describe("docs/api-locale.md", () => {
  it("documents every command of the registry", () => {
    const documented = documentedNames();
    for (const command of Object.keys(COMMAND_ARGUMENTS)) {
      expect(documented, `commande ${command} absente de docs/api-locale.md`).toContain(command);
    }
  });

  it("documents every app event", () => {
    const declared = declaredEventTypes();
    expect(declared.length).toBeGreaterThan(0);
    const documented = documentedNames();
    for (const event of declared) {
      expect(documented, `événement ${event} absent de docs/api-locale.md`).toContain(event);
    }
  });
});
