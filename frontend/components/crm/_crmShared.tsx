import { useEffect, useState, type ReactNode } from 'react';

import { Modal } from '@/components/shared/Modal';

/** Classes da pílula colorida de uma opção (token de cor → bg/text). */
export function pilulaCor(cor?: string | null): string {
  switch (cor) {
    case 'red':
      return 'bg-red-100 text-red-700';
    case 'orange':
      return 'bg-orange-100 text-orange-700';
    case 'yellow':
      return 'bg-yellow-100 text-yellow-800';
    case 'green':
      return 'bg-green-100 text-green-700';
    case 'blue':
      return 'bg-blue-100 text-blue-700';
    case 'purple':
      return 'bg-purple-100 text-purple-700';
    case 'gray':
      return 'bg-gray-100 text-gray-600';
    default:
      return 'bg-bg-alt text-ink-soft';
  }
}

export function Campo({
  label,
  children,
  span2,
}: {
  label: string;
  children: ReactNode;
  span2?: boolean;
}) {
  return (
    <label className={`flex flex-col gap-1.5 ${span2 ? 'md:col-span-2' : ''}`}>
      <span className="text-[12px] font-medium text-ink-soft">{label}</span>
      {children}
    </label>
  );
}

export function SelectCampo({
  label,
  value,
  opcoes,
  onChange,
  span2,
  vazioLabel = '—',
}: {
  label: string;
  value?: string | null;
  opcoes?: string[];
  onChange: (v: string) => void;
  span2?: boolean;
  vazioLabel?: string;
}) {
  return (
    <Campo label={label} span2={span2}>
      <select
        className="input"
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">{vazioLabel}</option>
        {(opcoes ?? []).map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </Campo>
  );
}

export function MultiCampo({
  label,
  valores,
  opcoes,
  onChange,
}: {
  label: string;
  valores: string[];
  opcoes?: string[];
  onChange: (v: string[]) => void;
}) {
  const toggle = (o: string) =>
    onChange(valores.includes(o) ? valores.filter((x) => x !== o) : [...valores, o]);
  return (
    <Campo label={label} span2>
      <div className="flex flex-wrap gap-1.5">
        {(opcoes ?? []).map((o) => {
          const on = valores.includes(o);
          return (
            <button
              key={o}
              type="button"
              onClick={() => toggle(o)}
              className={`text-[12px] px-2.5 py-1 rounded-full border transition-colors ${
                on
                  ? 'bg-brand text-white border-brand'
                  : 'bg-surface text-ink-soft border-line hover:border-ink-mute'
              }`}
            >
              {o}
            </button>
          );
        })}
      </div>
    </Campo>
  );
}

export function Info({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <span>
      <span className="text-ink-mute">{rotulo}:</span>{' '}
      <span className="text-ink">{valor}</span>
    </span>
  );
}

export function LinkExt({ href, label }: { href: string; label: string }) {
  const url = href.startsWith('http') ? href : `https://${href}`;
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="text-brand hover:underline"
    >
      {label} ↗
    </a>
  );
}

export function Bloco({
  titulo,
  children,
}: {
  titulo: string;
  children: ReactNode;
}) {
  return (
    <div>
      <h3 className="font-display font-semibold text-[13px] tracking-tight text-ink m-0 mb-2">
        {titulo}
      </h3>
      {children}
    </div>
  );
}

export function ConfirmarExclusao({
  titulo,
  alvo,
  carregando,
  onConfirmar,
  onCancelar,
}: {
  titulo: string;
  alvo: string;
  carregando?: boolean;
  onConfirmar: () => void;
  onCancelar: () => void;
}) {
  return (
    <Modal open onClose={onCancelar} title={titulo}>
      <p className="text-[14px] text-ink-soft m-0 mb-5">
        Excluir <span className="font-medium text-ink">{alvo}</span>? Essa ação
        não pode ser desfeita.
      </p>
      <div className="flex justify-end gap-3">
        <button type="button" className="btn-ghost" onClick={onCancelar}>
          Cancelar
        </button>
        <button
          type="button"
          className="btn-danger disabled:opacity-40"
          onClick={onConfirmar}
          disabled={carregando}
        >
          {carregando ? 'Excluindo…' : 'Excluir'}
        </button>
      </div>
    </Modal>
  );
}

/** Segmented control Lista/Kanban (e afins). */
export function VistaToggle<T extends string>({
  vista,
  vistas,
  onChange,
}: {
  vista: T;
  vistas: { id: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="inline-flex rounded-md border border-line overflow-hidden text-[13px]">
      {vistas.map((v) => (
        <button
          key={v.id}
          type="button"
          onClick={() => onChange(v.id)}
          className={`px-3 py-1.5 font-medium transition-colors ${
            vista === v.id
              ? 'bg-brand text-white'
              : 'bg-surface text-ink-soft hover:text-ink'
          }`}
        >
          {v.label}
        </button>
      ))}
    </div>
  );
}

/**
 * Kanban genérico com drag entre colunas. Agrupa `itens` por `statusDe`, ordena
 * as colunas por `ordem` (resto no fim), pinta o título pela cor da opção e
 * chama `onMover` ao soltar um card noutra coluna. Card via `renderCard`.
 */
export function KanbanGenerico<T extends { id: string }>({
  itens,
  ordem,
  statusDe,
  cores,
  semLabel = '(sem status)',
  onMover,
  onAbrir,
  renderCard,
}: {
  itens: T[];
  ordem: string[];
  statusDe: (it: T) => string | null | undefined;
  cores?: Record<string, string>;
  semLabel?: string;
  onMover: (it: T, status: string) => void;
  onAbrir: (it: T) => void;
  renderCard: (it: T) => ReactNode;
}) {
  const [arrastando, setArrastando] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  // Override otimista: move o card na hora; some quando os dados reais chegam.
  const [override, setOverride] = useState<Record<string, string>>({});
  useEffect(() => setOverride({}), [itens]);

  const statusAtual = (it: T) => override[it.id] ?? statusDe(it) ?? semLabel;

  const grupos: Record<string, T[]> = {};
  for (const it of itens) {
    (grupos[statusAtual(it)] ??= []).push(it);
  }
  const conhecidas = ordem.filter((s) => grupos[s]);
  const resto = Object.keys(grupos).filter((s) => !ordem.includes(s));
  const colunas = [...new Set([...conhecidas, ...resto])];

  function soltar(status: string) {
    const id = arrastando;
    setArrastando(null);
    setHover(null);
    if (!id || status === semLabel) return;
    const it = itens.find((x) => x.id === id);
    if (it && statusAtual(it) !== status) {
      setOverride((o) => ({ ...o, [id]: status })); // move já
      onMover(it, status);
    }
  }

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {colunas.map((status) => (
        <section
          key={status}
          onDragOver={(e) => {
            e.preventDefault();
            setHover(status);
          }}
          onDragLeave={() => setHover((h) => (h === status ? null : h))}
          onDrop={() => soltar(status)}
          className={`min-w-[270px] w-[270px] shrink-0 rounded-lg p-1 transition-colors ${
            hover === status ? 'bg-brand-soft/40' : ''
          }`}
        >
          <div className="flex items-center justify-between mb-3 px-1">
            <span
              className={`text-[12.5px] font-medium px-2 py-0.5 rounded-full ${pilulaCor(
                cores?.[status],
              )}`}
            >
              {status}
            </span>
            <span className="text-[12px] text-ink-mute font-mono">
              {grupos[status].length}
            </span>
          </div>
          <div className="flex flex-col gap-2.5 min-h-[80px]">
            {grupos[status].map((it) => (
              <div
                key={it.id}
                draggable
                onDragStart={() => setArrastando(it.id)}
                onDragEnd={() => setArrastando(null)}
                onClick={() => onAbrir(it)}
                className={`card p-3 cursor-pointer hover:border-brand/40 ${
                  arrastando === it.id ? 'opacity-40' : ''
                }`}
              >
                {renderCard(it)}
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
