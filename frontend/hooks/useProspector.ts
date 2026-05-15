import { useCallback, useState } from 'react';

import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';
import type {
  LeadHistoryItem,
  ProspectorManualRequest,
  ProspectorPreviewResponse,
  ProspectorRunResponse,
} from '@/lib/types';

export function useProspectorHistory(limit: number = 20) {
  const result = useFetch(
    () => api.prospectorHistory(limit),
    [limit],
  );

  const items: LeadHistoryItem[] = result.data?.items ?? [];
  const total: number = result.data?.total ?? 0;

  return { ...result, items, total };
}


interface MutationState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

export interface UseProspectorMutationResult<T> extends MutationState<T> {
  execute: (body: ProspectorManualRequest) => Promise<T | null>;
  reset: () => void;
  cancel: () => void;
}

function useProspectorMutation<T>(
  apiCall: (body: ProspectorManualRequest, opts?: { signal?: AbortSignal }) => Promise<T>,
): UseProspectorMutationResult<T> {
  const [state, setState] = useState<MutationState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const [controller, setController] = useState<AbortController | null>(null);

  const execute = useCallback(
    async (body: ProspectorManualRequest): Promise<T | null> => {
      controller?.abort();
      const newController = new AbortController();
      setController(newController);

      setState({ data: null, loading: true, error: null });
      try {
        const data = await apiCall(body, { signal: newController.signal });
        setState({ data, loading: false, error: null });
        return data;
      } catch (err) {
        if (newController.signal.aborted) {
          return null;
        }
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
    },
    [apiCall, controller],
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  const cancel = useCallback(() => {
    controller?.abort();
    setState({ data: null, loading: false, error: null });
  }, [controller]);

  return { ...state, execute, reset, cancel };
}

export function useProspectorPreview() {
  return useProspectorMutation<ProspectorPreviewResponse>(api.prospectorPreview);
}

export function useProspectorRun() {
  return useProspectorMutation<ProspectorRunResponse>(api.prospectorRun);
}
