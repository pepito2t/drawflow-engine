import { useEffect, useRef, useState } from "react";

/** Follows `value` but changes at most once per `intervalMs`, ending on the latest value. */
export function useThrottledValue<T>(value: T, intervalMs: number): T {
  const [shown, setShown] = useState(value);
  const shownAt = useRef(0);

  useEffect(() => {
    const delay = Math.max(0, intervalMs - (Date.now() - shownAt.current));
    const timer = setTimeout(() => {
      shownAt.current = Date.now();
      setShown(value);
    }, delay);
    return () => {
      clearTimeout(timer);
    };
  }, [value, intervalMs]);

  return shown;
}
