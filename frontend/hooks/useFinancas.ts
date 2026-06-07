import { useFetch } from './useFetch';
import { api } from '@/lib/api';
import { FINANCAS_USUARIO_ID } from '@/lib/financas';
import type { Conta, ResumoMes } from '@/lib/types';

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
