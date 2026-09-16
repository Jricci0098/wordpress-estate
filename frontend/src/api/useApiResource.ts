import { useEffect, useState } from "react";

interface ApiResourceState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useApiResource<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
): ApiResourceState<T> {
  const [state, setState] = useState<ApiResourceState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;
    setState({ data: null, loading: true, error: null });

    fetcher()
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : "Unknown error";
          setState({ data: null, loading: false, error: message });
        }
      });

    return () => {
      cancelled = true;
    };
  }, deps);

  return state;
}
