import { open } from "@tauri-apps/plugin-dialog";

export async function pickPaths(options: {
  directory: boolean;
  multiple: boolean;
  title: string;
}): Promise<string[]> {
  const selection = await open(options);
  if (selection === null) {
    return [];
  }
  return Array.isArray(selection) ? selection : [selection];
}
