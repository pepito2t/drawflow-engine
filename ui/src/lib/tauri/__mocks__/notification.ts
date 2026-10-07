export interface SentNotification {
  title: string;
  body: string;
}

export const sentNotifications: SentNotification[] = [];
let windowFocused = true;

export function setWindowFocused(focused: boolean): void {
  windowFocused = focused;
}

export function resetFakeNotifications(): void {
  sentNotifications.length = 0;
  windowFocused = true;
}

export function isWindowFocused(): Promise<boolean> {
  return Promise.resolve(windowFocused);
}

export function notify(title: string, body: string): Promise<void> {
  sentNotifications.push({ title, body });
  return Promise.resolve();
}
