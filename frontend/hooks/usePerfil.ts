import { useCallback, useState } from 'react';

import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';
import type { PerfilMestre } from '@/lib/types';

export function usePerfil() {
  const result = useFetch<PerfilMestre | null>(() => api.perfilGet(), []);
  return { ...result, perfil: result.data ?? null };
}

export function useSalvarPerfil() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const salvar = useCallback(
    async (perfil: PerfilMestre): Promise<PerfilMestre | null> => {
      setLoading(true);
      setError(null);
      try {
        return await api.perfilSalvar(perfil);
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err
            : new ApiError(err instanceof Error ? err.message : 'Erro', 0),
        );
        return null;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  return { salvar, loading, error };
}
