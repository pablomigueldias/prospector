import { useCallback, useState } from 'react';

import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';
import type {
  GerarImagemLinkedinRequest,
  LinkedinBriefRequest,
  LinkedinConta,
  LinkedinGerarRequest,
  LinkedinPost,
  LinkedinPostCreate,
  LinkedinPostUpdate,
  LinkedinRedacao,
  LinkedinStatus,
} from '@/lib/types';

function toApiError(err: unknown): ApiError {
  return err instanceof ApiError
    ? err
    : new ApiError(err instanceof Error ? err.message : 'Erro desconhecido', 0);
}

/** Lista posts (filtra por status/conta). Ambos entram como deps do refetch. */
export function useLinkedinPosts(status?: LinkedinStatus, conta?: LinkedinConta) {
  const result = useFetch<LinkedinPost[]>(
    () => api.linkedinListar(status, conta),
    [status, conta],
  );
  return { ...result, posts: result.data ?? [] };
}

export function useLinkedinActions() {
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
    (body: LinkedinPostCreate) =>
      wrap<LinkedinPost>(() => api.linkedinCriar(body))(),
    [],
  );
  const atualizar = useCallback(
    (id: string, body: LinkedinPostUpdate) =>
      wrap<LinkedinPost>(() => api.linkedinAtualizar(id, body))(),
    [],
  );
  const mudarStatus = useCallback(
    (id: string, status: LinkedinStatus) =>
      wrap<LinkedinPost>(() => api.linkedinMudarStatus(id, status))(),
    [],
  );
  const remover = useCallback(
    (id: string) => wrap<void>(() => api.linkedinRemover(id))(),
    [],
  );
  const redigir = useCallback(
    (brief: LinkedinBriefRequest) =>
      wrap<LinkedinRedacao>(() => api.linkedinRedigir(brief))(),
    [],
  );
  const gerar = useCallback(
    (req: LinkedinGerarRequest) =>
      wrap<LinkedinPost[]>(() => api.linkedinGerar(req))(),
    [],
  );
  const sugerirMidia = useCallback(
    (id: string) => wrap<LinkedinPost>(() => api.linkedinSugerirMidia(id))(),
    [],
  );
  const gerarImagem = useCallback(
    (id: string, req: GerarImagemLinkedinRequest) =>
      wrap<LinkedinPost>(() => api.linkedinGerarImagem(id, req))(),
    [],
  );

  return {
    loading,
    error,
    criar,
    atualizar,
    mudarStatus,
    remover,
    redigir,
    gerar,
    sugerirMidia,
    gerarImagem,
  };
}
