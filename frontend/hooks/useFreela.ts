import { useCallback, useState } from 'react';

import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';
import type {
  FreelaAnalisarResponse,
  FreelaChecklist,
  FreelaCliente,
  FreelaClienteCreate,
  FreelaExtrairProjeto,
  FreelaPrecificarRequest,
  FreelaPrecificarResponse,
  FreelaProjeto,
  FreelaProjetoCreate,
  FreelaProposta,
  FreelaPropostaCreate,
  FreelaNegociarResponse,
  FreelaRedigirResponse,
  FreelaStatus,
} from '@/lib/types';

export function useFreelaKanban() {
  const result = useFetch(() => api.freelaKanban(), []);
  return { ...result, colunas: result.data?.colunas ?? [] };
}

export function useFreelaMetricas() {
  return useFetch(() => api.freelaMetricas(), []);
}

export function useFreelaProjetos() {
  const result = useFetch(() => api.freelaProjetos(), []);
  return { ...result, items: result.data?.items ?? [], total: result.data?.total ?? 0 };
}

export function useFreelaPlataformas() {
  const result = useFetch(() => api.freelaPlataformas(), []);
  return { ...result, items: result.data ?? [] };
}

export function useFreelaClientes() {
  const result = useFetch(() => api.freelaClientes(), []);
  return { ...result, items: result.data ?? [] };
}

export function useFreelaProposta(id: string | undefined) {
  const result = useFetch<FreelaProposta>(
    () => (id ? api.freelaPropostaDetalhe(id) : Promise.reject(new Error('sem id'))),
    [id],
  );
  return { ...result, proposta: result.data };
}

function toApiError(err: unknown): ApiError {
  return err instanceof ApiError
    ? err
    : new ApiError(err instanceof Error ? err.message : 'Erro', 0);
}

/** Ações mutáveis do agente freela, com loading/erro próprios. */
export function useFreelaActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  function run<T>(fn: () => Promise<T>): Promise<T | null> {
    setLoading(true);
    setError(null);
    return fn()
      .catch((err) => {
        setError(toApiError(err));
        return null;
      })
      .finally(() => setLoading(false)) as Promise<T | null>;
  }

  const criarProjeto = useCallback(
    (body: FreelaProjetoCreate) => run<FreelaProjeto>(() => api.freelaProjetoCriar(body)),
    [],
  );
  const removerProjeto = useCallback(
    (id: string) => run<void>(() => api.freelaProjetoRemover(id)),
    [],
  );
  const extrairProjeto = useCallback(
    (texto: string) => run<FreelaExtrairProjeto>(() => api.freelaProjetoExtrair(texto)),
    [],
  );
  const analisarProjeto = useCallback(
    (id: string) => run<FreelaAnalisarResponse>(() => api.freelaProjetoAnalisar(id)),
    [],
  );
  const criarProposta = useCallback(
    (body: FreelaPropostaCreate) => run<FreelaProposta>(() => api.freelaPropostaCriar(body)),
    [],
  );
  const mudarStatus = useCallback(
    (id: string, status: FreelaStatus, motivo?: string | null) =>
      run<FreelaProposta>(() => api.freelaPropostaStatus(id, status, motivo)),
    [],
  );
  const removerProposta = useCallback(
    (id: string) => run<void>(() => api.freelaPropostaRemover(id)),
    [],
  );
  const atualizarProposta = useCallback(
    (id: string, body: Partial<FreelaProposta>) =>
      run<FreelaProposta>(() => api.freelaPropostaAtualizar(id, body)),
    [],
  );
  const redigirProposta = useCallback(
    (id: string, instrucoes?: string | null) =>
      run<FreelaRedigirResponse>(() => api.freelaPropostaRedigir(id, instrucoes)),
    [],
  );
  const negociarProposta = useCallback(
    (id: string, objecao: string) =>
      run<FreelaNegociarResponse>(() => api.freelaPropostaNegociar(id, objecao)),
    [],
  );
  const avaliarProposta = useCallback(
    (id: string) => run<FreelaChecklist>(() => api.freelaPropostaChecklist(id)),
    [],
  );
  const criarCliente = useCallback(
    (body: FreelaClienteCreate) => run<FreelaCliente>(() => api.freelaClienteCriar(body)),
    [],
  );
  const precificar = useCallback(
    (body: FreelaPrecificarRequest) =>
      run<FreelaPrecificarResponse>(() => api.freelaPrecificar(body)),
    [],
  );

  return {
    loading,
    error,
    criarProjeto,
    removerProjeto,
    extrairProjeto,
    analisarProjeto,
    criarProposta,
    mudarStatus,
    removerProposta,
    atualizarProposta,
    redigirProposta,
    negociarProposta,
    avaliarProposta,
    criarCliente,
    precificar,
  };
}
