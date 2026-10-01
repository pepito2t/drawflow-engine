import { useCallback, useState } from "react";

interface Attempt<T> {
  id: number;
  promise: Promise<T>;
}

interface RetryablePromise<T> extends Attempt<T> {
  retry: () => void;
}

export function useRetryablePromise<T>(load: () => Promise<T>): RetryablePromise<T> {
  const [attempt, setAttempt] = useState<Attempt<T>>(() => ({ id: 0, promise: load() }));
  const retry = useCallback(() => {
    setAttempt((current) => ({ id: current.id + 1, promise: load() }));
  }, [load]);
  return { ...attempt, retry };
}
