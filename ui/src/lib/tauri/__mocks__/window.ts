export const openedOutputs: string[] = [];

export function bringToFront(): Promise<void> {
  return Promise.resolve();
}

export function openOutput(path: string): Promise<void> {
  openedOutputs.push(path);
  return Promise.resolve();
}

export function openLogsFolder(): Promise<void> {
  return Promise.resolve();
}
