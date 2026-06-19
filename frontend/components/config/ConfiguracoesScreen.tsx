import { useEffect, useMemo, useState } from 'react';

import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';
import type { ConfigItem } from '@/lib/types';

type Valor = boolean | number | string;

/**
 * S3 — Configurações na UI. Lê o catálogo curado do backend e deixa o Pablo
 * mudar o comportamento do sistema (agendador, briefing, freela, LLM, alertas)
 * sem tocar em `.env`/`config.py`. As mudanças valem em runtime; as que afetam
 * o *agendamento* dos jobs avisam que precisam de restart.
 */
export function ConfiguracoesScreen() {
  const { data, loading, error, refetch } = useFetch<ConfigItem[]>(
    () => api.getConfig(),
    [],
  );

  // Estado local: o catálogo carregado + as edições pendentes (dirty).
  const [itens, setItens] = useState<ConfigItem[]>([]);
  const [edits, setEdits] = useState<Record<string, Valor>>({});
  const [salvando, setSalvando] = useState(false);
  const [msg, setMsg] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(
    null,
  );

  useEffect(() => {
    if (data) setItens(data);
  }, [data]);

  const porCategoria = useMemo(() => {
    return itens.reduce<Record<string, ConfigItem[]>>((acc, item) => {
      (acc[item.categoria] ??= []).push(item);
      return acc;
    }, {});
  }, [itens]);

  const dirty = Object.keys(edits).length > 0;
  const precisaRestart = useMemo(
    () =>
      itens.some(
        (i) => i.chave in edits && i.requer_restart && edits[i.chave] !== i.valor,
      ),
    [itens, edits],
  );

  function setEdit(chave: string, valor: Valor, original: Valor) {
    setMsg(null);
    setEdits((prev) => {
      const next = { ...prev };
      if (valor === original) delete next[chave];
      else next[chave] = valor;
      return next;
    });
  }

  function valorAtual(item: ConfigItem): Valor {
    return item.chave in edits ? edits[item.chave] : item.valor;
  }

  async function salvar() {
    if (!dirty) return;
    setSalvando(true);
    setMsg(null);
    try {
      const atualizado = await api.updateConfig(edits);
      setItens(atualizado);
      setEdits({});
      setMsg({
        tipo: 'ok',
        texto: precisaRestart
          ? 'Salvo. Algumas mudanças só valem após reiniciar a API.'
          : 'Salvo — já vale agora.',
      });
    } catch (e) {
      setMsg({
        tipo: 'erro',
        texto:
          e instanceof ApiError ? e.detail || e.message : 'Falha ao salvar.',
      });
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      <header>
        <div className="eyebrow mb-2">Self-service</div>
        <h1 className="font-display font-semibold text-2xl tracking-tight text-ink m-0">
          Configurações
        </h1>
        <p className="text-[15px] text-ink-soft mt-1 mb-0 max-w-[60ch]">
          Mude o comportamento do sistema aqui — sem mexer em código. O que
          afeta os horários dos jobs avisa quando precisa reiniciar a API.
        </p>
      </header>

      {loading && itens.length === 0 ? (
        <div className="card p-6 animate-pulse h-40" />
      ) : error ? (
        <div className="card p-5 border-red-300">
          <p className="text-[14px] text-red-600 m-0">
            Não consegui carregar ({error.status === 403
              ? 'sem permissão'
              : error.message}
            ).
          </p>
          <button className="btn-ghost mt-3" onClick={() => void refetch()}>
            Tentar de novo
          </button>
        </div>
      ) : (
        Object.entries(porCategoria).map(([categoria, lista]) => (
          <section key={categoria} className="card p-5">
            <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink mt-0 mb-4">
              {categoria}
            </h2>
            <div className="flex flex-col divide-y divide-line">
              {lista.map((item) => (
                <ConfigRow
                  key={item.chave}
                  item={item}
                  valor={valorAtual(item)}
                  dirty={item.chave in edits}
                  onChange={(v) => setEdit(item.chave, v, item.valor)}
                />
              ))}
            </div>
          </section>
        ))
      )}

      {/* Barra de salvar (fixa no fim do conteúdo) */}
      {itens.length > 0 && (
        <div className="flex items-center gap-3 sticky bottom-4">
          <button
            type="button"
            className="btn-primary"
            disabled={!dirty || salvando}
            onClick={() => void salvar()}
          >
            {salvando
              ? 'Salvando…'
              : dirty
                ? `Salvar ${Object.keys(edits).length} mudança(s)`
                : 'Tudo salvo'}
          </button>
          {dirty && (
            <button
              type="button"
              className="btn-ghost"
              disabled={salvando}
              onClick={() => {
                setEdits({});
                setMsg(null);
              }}
            >
              Descartar
            </button>
          )}
          {msg && (
            <span
              className={`text-[13px] ${
                msg.tipo === 'ok' ? 'text-emerald-600' : 'text-red-600'
              }`}
            >
              {msg.texto}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

function ConfigRow({
  item,
  valor,
  dirty,
  onChange,
}: {
  item: ConfigItem;
  valor: Valor;
  dirty: boolean;
  onChange: (v: Valor) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[14px] text-ink">{item.label}</span>
          {dirty && (
            <span className="text-[10px] font-mono uppercase tracking-wide text-amber-600">
              alterado
            </span>
          )}
          {item.requer_restart && (
            <span
              className="text-[10px] font-mono uppercase tracking-wide text-ink-faint"
              title="Só vale após reiniciar a API"
            >
              restart
            </span>
          )}
        </div>
        {item.ajuda && (
          <p className="text-[12px] text-ink-mute mt-0.5 mb-0">{item.ajuda}</p>
        )}
        {!item.sobrescrito && !dirty && (
          <p className="text-[11px] text-ink-faint mt-0.5 mb-0">
            padrão: {String(item.default)}
          </p>
        )}
      </div>
      <div className="shrink-0">
        <ConfigInput item={item} valor={valor} onChange={onChange} />
      </div>
    </div>
  );
}

function ConfigInput({
  item,
  valor,
  onChange,
}: {
  item: ConfigItem;
  valor: Valor;
  onChange: (v: Valor) => void;
}) {
  if (item.tipo === 'bool') {
    const on = Boolean(valor);
    return (
      <button
        type="button"
        role="switch"
        aria-checked={on}
        onClick={() => onChange(!on)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          on ? 'bg-brand' : 'bg-line'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            on ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    );
  }

  if (item.tipo === 'select') {
    return (
      <select
        className="input !py-1.5 !px-2 text-[14px]"
        value={String(valor)}
        onChange={(e) => onChange(e.target.value)}
      >
        {item.opcoes.map((op) => (
          <option key={op} value={op}>
            {op}
          </option>
        ))}
      </select>
    );
  }

  // int
  return (
    <input
      type="number"
      className="input !py-1.5 !px-2 text-[14px] w-24 text-right"
      value={Number(valor)}
      min={item.minimo ?? undefined}
      max={item.maximo ?? undefined}
      onChange={(e) => onChange(Number(e.target.value))}
    />
  );
}
