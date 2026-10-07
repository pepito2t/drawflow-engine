import { invoke as invokeCommand, type InvokeArgs } from "@tauri-apps/api/core";
import { bridgeErrorDraft } from "../console-capture";
import { recordConsoleEntry } from "./console";
import { describeBridgeError } from "./engine";

/**
 * Every bridge call goes through here so a refused command reaches the console once, whatever
 * the caller does with the error. Arguments are never logged: they may hold the access code.
 */
export async function invoke<T>(command: string, args?: InvokeArgs): Promise<T> {
  try {
    return await invokeCommand<T>(command, args);
  } catch (error: unknown) {
    recordConsoleEntry(bridgeErrorDraft(command, describeBridgeError(error)));
    throw error;
  }
}
