import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiError } from '@/lib/types';

export interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

export interface UseFetchResult<T> extends FetchState<T> {
  refetch: () => Promise<void>;
}

export function useFetch<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: React.DependencyList = [],
): UseFetchResult<T> {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const execute = useCallback(async (signal: AbortSignal) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await fetcherRef.current(signal);
      if (!signal.aborted) {
        setState({ data, loading: false, error: null });
      }
    } catch (err) {
      if (signal.aborted) return;
      const apiErr =
        err instanceof ApiError
          ? err
          : new ApiError(
              err instanceof Error ? err.message : 'Erro desconhecido',
              0,
            );
      setState({ data: null, loading: false, error: apiErr });
    }

  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void execute(controller.signal);
    return () => controller.abort();
    
  }, deps);

  const refetch = useCallback(async () => {
    const controller = new AbortController();
    await execute(controller.signal);
  }, [execute]);

  return { ...state, refetch };
}
