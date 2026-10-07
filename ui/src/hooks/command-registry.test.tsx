import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { COMMANDS } from "../lib/commands";
import { CommandProvider, useCommand, useCommands } from "./command-registry";

describe("command registry", () => {
  it("runs the registered handler with validated arguments and returns its data", async () => {
    const opened: string[] = [];
    const { result } = renderHook(
      () => {
        useCommand(COMMANDS.openTab, ({ moduleId }) => {
          opened.push(moduleId);
          return { opened: moduleId };
        });
        return useCommands();
      },
      { wrapper: CommandProvider },
    );

    const outcome = await result.current.execute(COMMANDS.openTab, { moduleId: "parts" });

    expect(outcome).toEqual({ ok: true, data: { opened: "parts" } });
    expect(opened).toEqual(["parts"]);
  });

  it("rejects unknown commands and invalid arguments without calling a handler", async () => {
    let calls = 0;
    const { result } = renderHook(
      () => {
        useCommand(COMMANDS.openTab, () => {
          calls += 1;
        });
        return useCommands();
      },
      { wrapper: CommandProvider },
    );

    expect((await result.current.execute("nope")).ok).toBe(false);
    expect((await result.current.execute(COMMANDS.openTab, { moduleId: "" })).ok).toBe(false);
    expect(calls).toBe(0);
  });

  it("reports a command whose screen is not mounted as unavailable", async () => {
    const { result } = renderHook(() => useCommands(), { wrapper: CommandProvider });

    const outcome = await result.current.execute(COMMANDS.openSettings);

    expect(outcome.ok).toBe(false);
    expect(outcome.ok ? "" : outcome.error).toContain("settings.open");
  });

  it("turns a handler failure into an error result", async () => {
    const { result } = renderHook(
      () => {
        useCommand(COMMANDS.openSettings, () => Promise.reject(new Error("Fenêtre fermée")));
        return useCommands();
      },
      { wrapper: CommandProvider },
    );

    expect(await result.current.execute(COMMANDS.openSettings)).toEqual({
      ok: false,
      error: "Fenêtre fermée",
    });
  });

  it("stops routing to a handler once it is unregistered", async () => {
    const { result } = renderHook(() => useCommands(), { wrapper: CommandProvider });
    const unregister = result.current.register(COMMANDS.openSettings, () => undefined);

    unregister();

    expect((await result.current.execute(COMMANDS.openSettings)).ok).toBe(false);
  });
});
