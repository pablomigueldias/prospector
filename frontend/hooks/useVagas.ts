import { useCallback, useState } from 'react';

import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';
import type {
  AnalisarVagaResponse,
  GerarCandidaturaResponse,
  Vaga,
  VagaCreate,
  VagaListItem,
} from '@/lib/types';

export function useVagas(status?: string) {
  const result = useFetch(() => api.vagasListar(status), [status]);
  const items: VagaListItem[] = result.data?.items ?? [];
  const total: number = result.data?.total ?? 0;
  return { ...result, items, total };
}

export function useVaga(id: string | undefined) {
  const result = useFetch<Vaga>(
    () =>
      id ? api.vagaDetalhe(id) : Promise.reject(new Error('sem id')),
    [id],
  );
  return { ...result, vaga: result.data };
}

function toApiError(err: unknown): ApiError {
  return err instanceof ApiError
    ? err
    : new ApiError(err instanceof Error ? err.message : 'Erro', 0);
}

/** Ações mutáveis de vaga, com loading/erro próprios. */
export function useVagaActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  function wrap<T>(fn: () => Promise<T>) {
    return async (): Promise<T | null> => {
      setLoading(true);
      setError(null);
      try {
        return await fn();
      } catch (err) {
        setError(toApiError(err));
        return null;
      } finally {
        setLoading(false);
      }
    };
  }

  const criar = useCallback(
    (body: VagaCreate) => wrap<Vaga>(() => api.vagaCriar(body))(),
    [],
  );
  const atualizar = useCallback(
    (id: string, body: Partial<Vaga>) =>
      wrap<Vaga>(() => api.vagaAtualizar(id, body))(),
    [],
  );
  const remover = useCallback(
    (id: string) => wrap<void>(() => api.vagaRemover(id))(),
    [],
  );
  const analisar = useCallback(
    (id: string) =>
      wrap<AnalisarVagaResponse>(() => api.vagaAnalisar(id))(),
    [],
  );
  const gerarCandidatura = useCallback(
    (id: string, gerarCarta: boolean, instrucoes?: string) =>
      wrap<GerarCandidaturaResponse>(() =>
        api.vagaGerarCandidatura(id, {
          gerar_carta: gerarCarta,
          instrucoes_extra: instrucoes || null,
        }),
      )(),
    [],
  );

  return {
    loading,
    error,
    criar,
    atualizar,
    remover,
    analisar,
    gerarCandidatura,
  };
}
