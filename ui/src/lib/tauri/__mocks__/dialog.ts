let nextSelection: string[] = [];

export function setNextSelection(paths: string[]): void {
  nextSelection = paths;
}

export function pickPaths(): Promise<string[]> {
  return Promise.resolve(nextSelection);
}

export function pickSavePath(): Promise<string | null> {
  return Promise.resolve(null);
}
