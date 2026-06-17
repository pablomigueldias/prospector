import { type VagasFiltro, type VagaStatus } from '@/lib/types';
import { FILTRO_VAZIO, STATUS_LABEL, STATUS_ORDEM } from './_shared';

// ── Barra de busca + filtros ──────────────────────────────────────

const MODELOS = ['remoto', 'híbrido', 'presencial'];

export function FiltrosBar({
  filtro,
  onMudar,
  total,
  loading,
}: {
  filtro: VagasFiltro;
  onMudar: (f: VagasFiltro) => void;
  total: number;
  loading: boolean;
}) {
  function set<K extends keyof VagasFiltro>(k: K, v: VagasFiltro[K]) {
    onMudar({ ...filtro, [k]: v });
  }

  const temFiltro =
    !!filtro.busca ||
    !!filtro.status ||
    filtro.match_min != null ||
    !!filtro.modelo ||
    !!filtro.fonte ||
    filtro.tem_rascunho != null;

  return (
    <div className="card p-4 mb-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1.5 grow min-w-[200px]">
          <label className="text-[11px] font-medium text-ink-mute">Buscar</label>
          <input
            className="input"
            placeholder="título ou empresa…"
            value={filtro.busca ?? ''}
            onChange={(e) => set('busca', e.target.value)}
          />
        </div>

        <SelectFiltro
          label="Status"
          value={filtro.status ?? ''}
          onChange={(v) => set('status', v as VagaStatus | '')}
          options={[
            ['', 'Todos'],
            ...STATUS_ORDEM.map((s) => [s, STATUS_LABEL[s]] as [string, string]),
          ]}
        />

        <SelectFiltro
          label="Modelo"
          value={filtro.modelo ?? ''}
          onChange={(v) => set('modelo', v)}
          options={[['', 'Qualquer'], ...MODELOS.map((m) => [m, m] as [string, string])]}
        />

        <div className="flex flex-col gap-1.5 w-[130px]">
          <label className="text-[11px] font-medium text-ink-mute">Fonte</label>
          <input
            className="input"
            placeholder="LinkedIn, Gupy…"
            value={filtro.fonte ?? ''}
            onChange={(e) => set('fonte', e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-1.5 w-[150px]">
          <label className="text-[11px] font-medium text-ink-mute">
            Match mín{filtro.match_min != null ? `: ${filtro.match_min}%` : ''}
          </label>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={filtro.match_min ?? 0}
            onChange={(e) => {
              const n = Number(e.target.value);
              set('match_min', n === 0 ? null : n);
            }}
          />
        </div>

        <SelectFiltro
          label="Ordenar"
          value={filtro.ordenar_por ?? 'match'}
          onChange={(v) => set('ordenar_por', (v || 'match') as 'match' | 'recentes')}
          options={[
            ['match', 'Maior match'],
            ['recentes', 'Mais recentes'],
          ]}
        />

        <label className="flex items-center gap-1.5 text-[12px] text-ink-soft pb-2">
          <input
            type="checkbox"
            checked={filtro.tem_rascunho === true}
            onChange={(e) => set('tem_rascunho', e.target.checked ? true : null)}
          />
          tem rascunho
        </label>
      </div>

      <div className="flex items-center justify-between mt-3">
        <span className="text-[12px] text-ink-mute">
          {loading ? 'filtrando…' : `${total} vaga(s)`}
        </span>
        {temFiltro && (
          <button
            type="button"
            className="text-[12px] text-brand hover:underline"
            onClick={() => onMudar(FILTRO_VAZIO)}
          >
            limpar filtros
          </button>
        )}
      </div>
    </div>
  );
}

function SelectFiltro({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: [string, string][];
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[11px] font-medium text-ink-mute">{label}</label>
      <select
        className="input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map(([v, rotulo]) => (
          <option key={v} value={v}>
            {rotulo}
          </option>
        ))}
      </select>
    </div>
  );
}

