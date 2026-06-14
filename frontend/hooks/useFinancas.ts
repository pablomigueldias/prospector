import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import { FINANCAS_USUARIO_ID } from '@/lib/financas';
import type {
  Cartao,
  CategoriaTreeItem,
  Comprovante,
  FaturasCartao,
  Conta,
  LeituraConsumo,
  ProjecaoFaturas,
  Recorrencia,
  RelatorioResponse,
  ResumoMes,
  TransacaoFiltro,
  TransacaoListItem,
} from '@/lib/types';

export function useResumoMes(ano: number, mes: number) {
  const result = useFetch<ResumoMes>(
    () => api.financasResumo(FINANCAS_USUARIO_ID, ano, mes),
    [ano, mes],
  );
  return { ...result, resumo: result.data };
}

export function useRelatorio(
  ano: number,
  mes: number,
  meses = 6,
  filtro?: { contaId?: string; categoriaId?: string },
  enabled = true,
) {
  const contaId = filtro?.contaId ?? '';
  const categoriaId = filtro?.categoriaId ?? '';
  const result = useFetch<RelatorioResponse | null>(
    () =>
      enabled
        ? api.financasRelatorio(FINANCAS_USUARIO_ID, ano, mes, meses, {
            contaId: contaId || undefined,
            categoriaId: categoriaId || undefined,
          })
        : Promise.resolve(null),
    [ano, mes, meses, contaId, categoriaId, enabled],
  );
  return { ...result, relatorio: result.data };
}

export function useContas(apenasAtivas = false) {
  const result = useFetch(
    () => api.financasContas(FINANCAS_USUARIO_ID, apenasAtivas),
    [apenasAtivas],
  );
  const contas: Conta[] = result.data?.items ?? [];
  const total: number = result.data?.total ?? 0;
  return { ...result, contas, total };
}

export function useCartoes() {
  const result = useFetch(() => api.financasCartoes(FINANCAS_USUARIO_ID), []);
  const cartoes: Cartao[] = result.data?.items ?? [];
  return { ...result, cartoes };
}

export function useCartaoFaturas(cartaoId: string) {
  const result = useFetch<FaturasCartao>(
    () => api.financasCartaoFaturas(cartaoId),
    [cartaoId],
  );
  return { ...result, dados: result.data };
}

export function useProjecaoCartoes(meses = 6, recarregar = 0) {
  const result = useFetch<ProjecaoFaturas>(
    () => api.financasProjecaoCartoes(meses),
    [meses, recarregar],
  );
  return { ...result, projecao: result.data };
}

export function useLeituras(tipo?: string) {
  const result = useFetch(
    () => api.financasLeituras(FINANCAS_USUARIO_ID, tipo),
    [tipo],
  );
  const leituras: LeituraConsumo[] = result.data?.items ?? [];
  return { ...result, leituras };
}

export function useTransacoes(filtro: TransacaoFiltro) {
  const result = useFetch(
    () => api.financasTransacoes(filtro),
    [
      filtro.ano,
      filtro.mes,
      filtro.conta_id,
      filtro.categoria_id,
      filtro.tipo,
      filtro.busca,
      filtro.limit,
      filtro.offset,
    ],
  );
  const transacoes: TransacaoListItem[] = result.data?.items ?? [];
  const total: number = result.data?.total ?? 0;
  return { ...result, transacoes, total };
}

export function useCategorias() {
  const result = useFetch(() => api.financasCategorias(), []);
  const arvore: CategoriaTreeItem[] = result.data?.items ?? [];
  return { ...result, arvore };
}

export function useRecorrencias() {
  const result = useFetch(() => api.financasRecorrencias(), []);
  const recorrencias: Recorrencia[] = result.data?.items ?? [];
  const total: number = result.data?.total ?? 0;
  return { ...result, recorrencias, total };
}

export function useComprovantes(tipo?: string) {
  const result = useFetch(
    () => api.financasComprovantes(FINANCAS_USUARIO_ID, tipo),
    [tipo],
  );
  const comprovantes: Comprovante[] = result.data?.items ?? [];
  return { ...result, comprovantes };
}
