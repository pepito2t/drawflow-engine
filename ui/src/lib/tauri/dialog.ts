import { open, save } from "@tauri-apps/plugin-dialog";

export interface FileFilter {
  name: string;
  extensions: string[];
}

export async function pickPaths(options: {
  directory: boolean;
  multiple: boolean;
  title: string;
  filters?: FileFilter[];
}): Promise<string[]> {
  const selection = await open(options);
  if (selection === null) {
    return [];
  }
  return Array.isArray(selection) ? selection : [selection];
}

export function pickSavePath(options: {
  title: string;
  defaultPath: string;
  filters: FileFilter[];
}): Promise<string | null> {
  return save(options);
}
