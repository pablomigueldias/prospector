import { useCallback, useState } from 'react';

import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';
import type {
  BlogBriefRequest,
  BlogPauta,
  BlogPautaGerarRequest,
  BlogPautaManualCreate,
  BlogPautaStatus,
  BlogPautaUpdate,
  BlogPostAdmin,
  BlogPostCreate,
  BlogPostUpdate,
  BlogRedacao,
  BlogStatus,
  CapaSugestoesResponse,
  ChecklistSeo,
  ChecklistSeoRequest,
  GerarImagemConteudoRequest,
  GerarImagemRequest,
  ImagemConteudoSugestoesResponse,
} from '@/lib/types';

function toApiError(err: unknown): ApiError {
  return err instanceof ApiError
    ? err
    : new ApiError(err instanceof Error ? err.message : 'Erro desconhecido', 0);
}

/** Lista posts (todos ou por status). `status` entra como dep do refetch. */
export function useBlogPosts(status?: BlogStatus) {
  const result = useFetch<BlogPostAdmin[]>(
    () => api.blogListar(status),
    [status],
  );
  return { ...result, posts: result.data ?? [] };
}

/** Backlog de pautas (ordenado por score no backend). */
export function useBlogPautas(status?: BlogPautaStatus) {
  const result = useFetch<BlogPauta[]>(() => api.blogPautas(status), [status]);
  return { ...result, pautas: result.data ?? [] };
}

export function useBlogActions() {
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
    (body: BlogPostCreate) => wrap<BlogPostAdmin>(() => api.blogCriar(body))(),
    [],
  );
  const atualizar = useCallback(
    (id: string, body: BlogPostUpdate) =>
      wrap<BlogPostAdmin>(() => api.blogAtualizar(id, body))(),
    [],
  );
  const mudarStatus = useCallback(
    (id: string, status: BlogStatus) =>
      wrap<BlogPostAdmin>(() => api.blogMudarStatus(id, status))(),
    [],
  );
  const remover = useCallback(
    (id: string) => wrap<void>(() => api.blogRemover(id))(),
    [],
  );
  const redigir = useCallback(
    (brief: BlogBriefRequest) =>
      wrap<BlogRedacao>(() => api.blogRedigir(brief))(),
    [],
  );
  const checklist = useCallback(
    (payload: ChecklistSeoRequest) =>
      wrap<ChecklistSeo>(() => api.blogChecklist(payload))(),
    [],
  );

  const gerarPautas = useCallback(
    (req: BlogPautaGerarRequest) =>
      wrap<BlogPauta[]>(() => api.blogGerarPautas(req))(),
    [],
  );
  const criarPauta = useCallback(
    (body: BlogPautaManualCreate) =>
      wrap<BlogPauta>(() => api.blogCriarPauta(body))(),
    [],
  );
  const atualizarPauta = useCallback(
    (id: string, body: BlogPautaUpdate) =>
      wrap<BlogPauta>(() => api.blogAtualizarPauta(id, body))(),
    [],
  );
  const removerPauta = useCallback(
    (id: string) => wrap<void>(() => api.blogRemoverPauta(id))(),
    [],
  );
  const escreverPauta = useCallback(
    (id: string) => wrap<BlogPostAdmin>(() => api.blogEscreverPauta(id))(),
    [],
  );
  const sugerirCapas = useCallback(
    (id: string) =>
      wrap<CapaSugestoesResponse>(() => api.blogSugerirCapas(id))(),
    [],
  );
  const gerarImagem = useCallback(
    (id: string, body: GerarImagemRequest) =>
      wrap<BlogPostAdmin>(() => api.blogGerarImagem(id, body))(),
    [],
  );
  const uploadImagem = useCallback(
    (id: string, arquivo: File, papel: 'cover' | 'secao' = 'cover', alt?: string) =>
      wrap<BlogPostAdmin>(() => api.blogUploadImagem(id, arquivo, papel, alt))(),
    [],
  );
  const gerarImagensConteudo = useCallback(
    (id: string) => wrap<BlogPostAdmin>(() => api.blogGerarImagensConteudo(id))(),
    [],
  );
  const sugerirImagensConteudo = useCallback(
    (id: string) =>
      wrap<ImagemConteudoSugestoesResponse>(
        () => api.blogSugerirImagensConteudo(id),
      )(),
    [],
  );
  const inserirImagemConteudo = useCallback(
    (id: string, body: GerarImagemConteudoRequest) =>
      wrap<BlogPostAdmin>(() => api.blogInserirImagemConteudo(id, body))(),
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
    checklist,
    gerarPautas,
    criarPauta,
    atualizarPauta,
    removerPauta,
    escreverPauta,
    sugerirCapas,
    gerarImagem,
    uploadImagem,
    gerarImagensConteudo,
    sugerirImagensConteudo,
    inserirImagemConteudo,
  };
}
