/**
 * Encargos por atraso de boleto: multa (uma vez) + juros de mora (por dia).
 * Espelha `app/api/services/financas/encargos.py` no backend — a conta na hora
 * de pagar usa a mesma fórmula e a mesma data, então o valor mostrado bate com
 * o que é efetivado.
 */

function paraData(iso: string): Date {
  return new Date(iso.slice(0, 10) + 'T00:00:00');
}

function num(v: string | number | null | undefined): number {
  const n = typeof v === 'string' ? Number(v) : v;
  return Number.isFinite(n as number) ? (n as number) : 0;
}

export interface Encargos {
  dias: number;
  multa: number;
  juros: number;
  total: number;
}

/**
 * Multa + juros sobre `valor` até `referencia` (ISO YYYY-MM-DD). Tudo zero se
 * não há vencimento, está no prazo, ou não há encargos. Juros mensais viram
 * diários linearmente (÷30).
 */
export function calcularEncargos(
  valor: string | number,
  vencimento: string | null | undefined,
  multaPercentual: string | number | null | undefined,
  jurosMensalPercentual: string | number | null | undefined,
  referencia: string,
): Encargos {
  const zero: Encargos = { dias: 0, multa: 0, juros: 0, total: 0 };
  if (!vencimento) return zero;
  const venc = paraData(vencimento);
  const ref = paraData(referencia);
  const dias = Math.round((ref.getTime() - venc.getTime()) / 86_400_000);
  if (dias <= 0) return zero;

  const base = num(valor);
  const multaPct = num(multaPercentual);
  const jurosPct = num(jurosMensalPercentual);
  const multa = (base * multaPct) / 100;
  const juros = ((base * jurosPct) / 100) * (dias / 30);
  const round = (n: number) => Math.round(n * 100) / 100;
  const m = round(multa);
  const j = round(juros);
  return { dias, multa: m, juros: j, total: round(m + j) };
}
