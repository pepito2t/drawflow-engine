import { describe, expect, it } from "vitest";
import pluginTable from "../../../streamdock/src/commands.ts?raw";
import { COMMAND_ARGUMENTS, type CommandId } from "./commands";

const PLUGIN_COMMAND_ID = /id: "([a-z][a-z.-]*)"/g;
// A query answered in `data`, already served by the plugin's own keys: pointless on a generic key.
const QUERIES: readonly CommandId[] = ["app.state"];

function pluginCommandIds(): string[] {
  return [...pluginTable.matchAll(PLUGIN_COMMAND_ID)].flatMap((match) => match[1] ?? []);
}

function argumentLessCommands(): CommandId[] {
  return (Object.keys(COMMAND_ARGUMENTS) as CommandId[]).filter(
    (id) => !QUERIES.includes(id) && COMMAND_ARGUMENTS[id].safeParse({}).success,
  );
}

describe("streamdock/src/commands.ts", () => {
  it("offers every command of the registry that needs no argument", () => {
    const offered = pluginCommandIds();
    expect(offered.length).toBeGreaterThan(0);
    for (const id of argumentLessCommands()) {
      expect(offered, `commande ${id} absente de la touche Commande du Stream Dock`).toContain(id);
    }
  });

  it("only offers commands of the registry that accept an empty argument", () => {
    const accepted = argumentLessCommands();
    for (const id of pluginCommandIds()) {
      expect(accepted, `commande ${id} inconnue ou exigeant un argument`).toContain(id);
    }
  });
});
