import type { KeyboardEvent } from "react";
import { targetTabIndex } from "../lib/tablist-navigation";

const TAB_SELECTOR = '[role="tab"]';

/** Arrow keys, Home and End move between the tabs of a vertical tab list and select the tab reached. */
export function onTablistKeyDown(event: KeyboardEvent<HTMLElement>): void {
  const tabs = Array.from(event.currentTarget.querySelectorAll<HTMLElement>(TAB_SELECTOR));
  const current = tabs.findIndex((tab) => tab === document.activeElement);
  const target = targetTabIndex(event.key, Math.max(current, 0), tabs.length);
  const tab = target === null ? undefined : tabs[target];
  if (!tab) {
    return;
  }
  event.preventDefault();
  tab.focus();
  tab.click();
}
