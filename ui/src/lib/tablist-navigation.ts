const PREVIOUS_KEY = "ArrowUp";
const NEXT_KEY = "ArrowDown";
const FIRST_KEY = "Home";
const LAST_KEY = "End";

/** Position of the tab a key moves to in a vertical tab list, wrapping at both ends; null if none. */
export function targetTabIndex(key: string, current: number, count: number): number | null {
  if (count === 0) {
    return null;
  }
  if (key === PREVIOUS_KEY) {
    return (current - 1 + count) % count;
  }
  if (key === NEXT_KEY) {
    return (current + 1) % count;
  }
  if (key === FIRST_KEY) {
    return 0;
  }
  if (key === LAST_KEY) {
    return count - 1;
  }
  return null;
}
