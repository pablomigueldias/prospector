import { useMemo, useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { useLeituras } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { ApiError, type LeituraConsumo } from '@/lib/types';

const TIPO_LABEL: Record<string, string> = {
  agua: '💧 Água',
  gas: '🔥 Gás',
  luz: '💡 Luz',
};

export function ConsumoSection() {
  const { leituras, loading, refetch } = useLeituras();
  const [registrar, setRegistrar] = useState(false);

  const porTipo = useMemo(() => {
    const m: Record<string, LeituraConsumo[]> = {};
    for (const l of leituras) {
      (m[l.tipo] ??= []).push(l);
    }
    return m;
  }, [leituras]);

  const tipos = Object.keys(porTipo);

  return (
    <div>
      <div className="flex justify-end mb-3">
        <button
          type="button"
          onClick={() => setRegistrar(true)}
          className="btn-ghost px-3.5 py-1.5 text-sm"
        >
          + Registrar leitura
        </button>
      </div>

      {loading ? (
        <div className="card p-4 h-[120px] animate-pulse" />
      ) : tipos.length === 0 ? (
        <div className="card p-6 text-center text-ink-soft text-sm">
          Sem leituras de consumo ainda. Chegam pelos boletos de condomínio — ou
          registre uma manualmente.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {tipos.map((tipo) => (
            <ConsumoCard key={tipo} tipo={tipo} leituras={porTipo[tipo]} />
          ))}
        </div>
      )}

      {registrar && (
        <LeituraForm
          onClose={() => setRegistrar(false)}
          onSaved={() => {
            setRegistrar(false);
            void refetch();
          }}
        />
      )}
    </div>
  );
}

function LeituraForm({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: () => void;
}) {
  const hoje = new Date();
  const [tipo, setTipo] = useState<'agua' | 'gas' | 'luz'>('agua');
  const [mes, setMes] = useState(
    `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}`,
  );
  const [atual, setAtual] = useState('');
  const [anterior, setAnterior] = useState('');
  const [valor, setValor] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  const num = (s: string) => Number(s.replace(',', '.'));
  const consumoPrevia =
    atual.trim() && anterior.trim() ? num(atual) - num(anterior) : null;

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!atual.trim() || !Number.isFinite(num(atual))) {
      return setErro('Informe a leitura atual.');
    }
    if (anterior.trim() && !Number.isFinite(num(anterior))) {
      return setErro('Leitura anterior inválida.');
    }
    if (valor.trim() && !Number.isFinite(num(valor))) {
      return setErro('Valor inválido.');
    }
    setSalvando(true);
    try {
      await api.financasCriarLeitura({
        tipo,
        mes_referencia: `${mes}-01`,
        leitura_atual: String(num(atual)),
        leitura_anterior: anterior.trim() ? String(num(anterior)) : null,
        valor: valor.trim() ? String(num(valor)) : null,
      });
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao registrar a leitura.');
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title="Registrar leitura de consumo">
      <form onSubmit={salvar} className="space-y-4">
        <div className="grid grid-cols-3 gap-2">
          {(['agua', 'gas', 'luz'] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTipo(t)}
              className={`py-2 rounded-lg border text-sm font-medium transition-colors ${
                tipo === t
                  ? 'border-brand bg-brand-soft text-brand-ink'
                  : 'border-line text-ink-soft hover:border-ink-mute'
              }`}
            >
              {TIPO_LABEL[t]}
            </button>
          ))}
        </div>

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Mês de referência
          </label>
          <input
            type="month"
            className="input"
            value={mes}
            onChange={(e) => setMes(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Leitura atual
            </label>
            <input
              className="input"
              value={atual}
              onChange={(e) => setAtual(e.target.value)}
              inputMode="decimal"
              placeholder="ex: 1234,5"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Leitura anterior (opcional)
            </label>
            <input
              className="input"
              value={anterior}
              onChange={(e) => setAnterior(e.target.value)}
              inputMode="decimal"
              placeholder="ex: 1220"
            />
          </div>
        </div>

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Valor da conta (opcional)
          </label>
          <input
            className="input"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            inputMode="decimal"
            placeholder="0,00"
          />
        </div>

        {consumoPrevia != null && consumoPrevia >= 0 && (
          <p className="text-[12.5px] text-ink-mute m-0">
            Consumo do mês: {consumoPrevia.toLocaleString('pt-BR')}
          </p>
        )}

        {erro && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
            {erro}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="btn-ghost px-4 py-2 text-sm">
            Cancelar
          </button>
          <button
            type="submit"
            disabled={salvando}
            className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
          >
            {salvando ? 'Salvando…' : 'Registrar'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ConsumoCard({ tipo, leituras }: { tipo: string; leituras: LeituraConsumo[] }) {
  const valores = leituras.map((l) => Number(l.consumo ?? 0));
  const max = Math.max(1, ...valores);
  const ultimo = valores[valores.length - 1] ?? 0;

  return (
    <div className="card p-4">
      <div className="flex items-baseline justify-between mb-3">
        <span className="font-medium text-ink">{TIPO_LABEL[tipo] ?? tipo}</span>
        <span className="text-ink-soft text-sm tabular-nums">
          {ultimo.toLocaleString('pt-BR')} <span className="text-ink-mute text-[11px]">último</span>
        </span>
      </div>
      <div className="flex items-end gap-1 h-12">
        {leituras.map((l) => {
          const v = Number(l.consumo ?? 0);
          const h = Math.round((v / max) * 100);
          return (
            <div
              key={l.id}
              className="flex-1 bg-brand-soft rounded-sm min-h-[2px]"
              style={{ height: `${h}%` }}
              title={`${l.mes_referencia}: ${v.toLocaleString('pt-BR')}`}
            />
          );
        })}
      </div>
    </div>
  );
}
