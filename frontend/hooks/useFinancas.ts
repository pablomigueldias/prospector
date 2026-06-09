import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import { FINANCAS_USUARIO_ID } from '@/lib/financas';
import type {
  Cartao,
  Comprovante,
  FaturasCartao,
  Conta,
  LeituraConsumo,
  ResumoMes,
} from '@/lib/types';

export function useResumoMes(ano: number, mes: number) {
  const result = useFetch<ResumoMes>(
    () => api.financasResumo(FINANCAS_USUARIO_ID, ano, mes),
    [ano, mes],
  );
  return { ...result, resumo: result.data };
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

export function useLeituras(tipo?: string) {
  const result = useFetch(
    () => api.financasLeituras(FINANCAS_USUARIO_ID, tipo),
    [tipo],
  );
  const leituras: LeituraConsumo[] = result.data?.items ?? [];
  return { ...result, leituras };
}

export function useComprovantes(tipo?: string) {
  const result = useFetch(
    () => api.financasComprovantes(FINANCAS_USUARIO_ID, tipo),
    [tipo],
  );
  const comprovantes: Comprovante[] = result.data?.items ?? [];
  return { ...result, comprovantes };
}
