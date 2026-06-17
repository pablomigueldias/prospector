import { type FaixaSalarial, type VagasFiltro, type VagaStatus } from '@/lib/types';

export const STATUS_LABEL: Record<VagaStatus, string> = {
  quero_candidatar: 'Quero candidatar',
  candidatei: 'Candidatei',
  respondeu: 'Respondeu',
  entrevista: 'Entrevista',
  fim: 'Encerrada',
};

export const STATUS_ORDEM: VagaStatus[] = [
  'quero_candidatar',
  'candidatei',
  'respondeu',
  'entrevista',
  'fim',
];

export const FILTRO_VAZIO: VagasFiltro = { ordenar_por: 'match' };

// ── pedaços reutilizáveis ─────────────────────────────────────────

export function Campo({
  label,
  obrigatorio,
  children,
}: {
  label: string;
  obrigatorio?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex items-center gap-1 text-xs font-medium text-ink-soft">
        {label}
        {obrigatorio && <span className="text-brand">*</span>}
      </label>
      {children}
    </div>
  );
}

export function Tags({
  titulo,
  itens,
  forte,
  ok,
}: {
  titulo: string;
  itens: string[];
  forte?: boolean;
  ok?: boolean;
}) {
  if (!itens || itens.length === 0) return null;
  const cls = ok
    ? 'bg-success-soft text-success-ink'
    : forte
      ? 'bg-brand-soft text-brand-ink'
      : 'bg-bg-alt text-ink-soft';
  return (
    <div className="mb-2.5">
      <div className="text-[11px] font-medium text-ink-mute mb-1">{titulo}</div>
      <div className="flex flex-wrap gap-1.5">
        {itens.map((t, i) => (
          <span
            key={i}
            className={`text-[12px] px-2 py-1 rounded-sm leading-snug ${cls}`}
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

function brl(v?: number | null): string | null {
  if (v == null) return null;
  return v.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  });
}

function faixa(min?: number | null, max?: number | null): string {
  const a = brl(min);
  const b = brl(max);
  if (a && b) return a === b ? a : `${a} – ${b}`;
  return a || b || '—';
}

export function BlocoSalario({ salario }: { salario: FaixaSalarial }) {
  const temFaixa =
    salario.pj_min != null ||
    salario.pj_max != null ||
    salario.clt_min != null ||
    salario.clt_max != null;
  if (!temFaixa && salario.pretensao_pj == null && salario.pretensao_clt == null) {
    return null;
  }

  return (
    <div className="mt-4 pt-4 border-t border-line">
      <div className="flex items-center gap-2 mb-2">
        <h4 className="font-display font-semibold text-sm text-ink m-0">
          Pretensão salarial
        </h4>
        <span className="font-mono text-[10px] text-ink-mute uppercase tracking-[0.06em]">
          estimativa de mercado
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        <div className="bg-bg-alt border border-line rounded p-3">
          <div className="font-mono text-[10px] uppercase tracking-[0.08em] text-ink-mute mb-1">
            PJ · R$/mês
          </div>
          <div className="text-[15px] font-semibold text-ink leading-tight">
            {faixa(salario.pj_min, salario.pj_max)}
          </div>
          {salario.pretensao_pj != null && (
            <div className="text-[12px] text-success-ink mt-1">
              pedir: <strong>{brl(salario.pretensao_pj)}</strong>
            </div>
          )}
        </div>
        <div className="bg-bg-alt border border-line rounded p-3">
          <div className="font-mono text-[10px] uppercase tracking-[0.08em] text-ink-mute mb-1">
            CLT · R$/mês
          </div>
          <div className="text-[15px] font-semibold text-ink leading-tight">
            {faixa(salario.clt_min, salario.clt_max)}
          </div>
          {salario.pretensao_clt != null && (
            <div className="text-[12px] text-success-ink mt-1">
              pedir: <strong>{brl(salario.pretensao_clt)}</strong>
            </div>
          )}
        </div>
      </div>

      {salario.base && (
        <p className="text-[12px] text-ink-soft mt-2">
          <span className="text-ink-mute">Base:</span> {salario.base}
        </p>
      )}
      {salario.observacao && (
        <p className="text-[12px] text-ink-mute mt-1 italic">{salario.observacao}</p>
      )}
    </div>
  );
}

export function MatchPill({ score, grande }: { score: number; grande?: boolean }) {
  const cor =
    score >= 70
      ? 'bg-success-soft text-success-ink'
      : score >= 40
        ? 'bg-brand-soft text-brand-ink'
        : 'bg-bg-alt text-ink-mute';
  return (
    <span
      className={[
        'font-mono rounded-sm whitespace-nowrap',
        grande ? 'text-sm px-2.5 py-1' : 'text-[10px] px-1.5 py-0.5',
        cor,
      ].join(' ')}
    >
      {score}%
    </span>
  );
}

export function StatusBadge({ status }: { status: VagaStatus }) {
  const cls: Record<VagaStatus, string> = {
    quero_candidatar: 'bg-bg-alt text-ink-soft',
    candidatei: 'bg-brand-soft text-brand-ink',
    respondeu: 'bg-success-soft text-success-ink',
    entrevista: 'bg-success-soft text-success-ink',
    fim: 'bg-bg-alt text-ink-mute',
  };
  return (
    <span
      className={`font-mono text-[10px] uppercase tracking-[0.06em] px-2 py-1 rounded-sm whitespace-nowrap ${cls[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}
