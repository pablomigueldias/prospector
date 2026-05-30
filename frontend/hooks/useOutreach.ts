import { useCallback, useState } from 'react';

import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';
import type {
  EmailItem,
  GerarRascunhosResponse,
  SyncResponse,
} from '@/lib/types';

export function useOutreachEmails(limit: number = 50) {
  const result = useFetch(() => api.outreachEmails(limit), [limit]);
  const items: EmailItem[] = result.data?.items ?? [];
  const total: number = result.data?.total ?? 0;
  return { ...result, items, total };
}

interface ActionState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

function useAction<T>(fn: (signal: AbortSignal) => Promise<T>) {
  const [state, setState] = useState<ActionState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const run = useCallback(async (): Promise<T | null> => {
    const controller = new AbortController();
    setState({ data: null, loading: true, error: null });
    try {
      const data = await fn(controller.signal);
      setState({ data, loading: false, error: null });
      return data;
    } catch (err) {
      const apiErr =
        err instanceof ApiError
          ? err
          : new ApiError(
              err instanceof Error ? err.message : 'Erro desconhecido',
              0,
            );
      setState({ data: null, loading: false, error: apiErr });
      return null;
    }
  }, [fn]);

  const reset = useCallback(
    () => setState({ data: null, loading: false, error: null }),
    [],
  );

  return { ...state, run, reset };
}

export function useOutreachGerar(limit: number | null, pausa: number = 8) {
  return useAction<GerarRascunhosResponse>((signal) =>
    api.outreachGerar({ limit, pausa }, { signal }),
  );
}

export function useOutreachSync() {
  return useAction<SyncResponse>((signal) => api.outreachSync({ signal }));
}