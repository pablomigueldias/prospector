import { useMemo, useState, type FormEvent } from 'react';

import { useCategorias } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias } from '@/lib/categorias';
import { formatBRL } from '@/lib/format';
import { ApiError, type Conta, type NluInterpretacao } from '@/lib/types';

/**
 * Caixa "digite o gasto" — interpreta texto livre com o mesmo NLU do bot
 * (`POST /api/financas/nlu/interpretar`), mostra o rascunho pra confirmar
 * (conta/categoria editáveis) e só então lança a transação.
 */
export function NluLancarSection({
  contas,
  onMutate,
}: {
  contas: Conta[];
  onMutate?: () => void;
}) {
  const { arvore } = useCategorias();
  const categorias = useMemo(() => achatarCategorias(arvore), [arvore]);

  const [texto, setTexto] = useState('');
  const [interpretando, setInterpretando] = useState(false);
  const [rascunho, setRascunho] = useState<NluInterpretacao | null>(null);
  const [contaId, setContaId] = useState('');
  const [categoriaId, setCategoriaId] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');
  const [ok, setOk] = useState('');

  async function interpretar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    setOk('');
    if (!texto.trim()) return;
    setInterpretando(true);
    try {
      const r = await api.financasNluInterpretar(texto.trim());
      setRascunho(r);
      setContaId(r.conta_id ?? contas[0]?.id ?? '');
      setCategoriaId(r.categoria_id ?? '');
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Não consegui interpretar.');
    } finally {
      setInterpretando(false);
    }
  }

  async function confirmar() {
    if (!rascunho) return;
    setErro('');
    if (!contaId) return setErro('Escolha a conta.');
    setSalvando(true);
    try {
      const body = {
        descricao: rascunho.descricao,
        valor_total: String(rascunho.valor),
        conta_id: contaId,
        categoria_id: categoriaId || null,
        data_competencia: rascunho.data || null,
        status: 'paga' as const,
      };
      if (rascunho.tipo === 'receita') {
        await api.financasLancarReceita(body);
      } else {
        await api.financasLancarDespesa(body);
      }
      setOk(`Lançado: ${rascunho.descricao} — ${formatBRL(rascunho.valor)}.`);
      setRascunho(null);
      setTexto('');
      onMutate?.();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao lançar.');
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="card p-4">
      <form onSubmit={interpretar} className="flex items-center gap-2">
        <input
          className="input flex-1"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder='Digite em linguagem natural — ex.: "gastei 30 no mercado com o VR"'
        />
        <button
          type="submit"
          disabled={interpretando || !texto.trim()}
          className="btn-primary px-4 py-2 text-sm disabled:opacity-50 shrink-0"
        >
          {interpretando ? 'Lendo…' : 'Interpretar'}
        </button>
      </form>

      {erro && <div className="text-sm text-red-600 mt-3">{erro}</div>}
      {ok && <div className="text-sm text-success mt-3">{ok}</div>}

      {rascunho && (
        <div className="mt-4 border-t border-line-soft pt-4 space-y-3">
          <div className="flex items-baseline justify-between">
            <span className="text-ink">
              <span
                className={`font-mono uppercase tracking-[0.08em] text-[10px] mr-2 ${
                  rascunho.tipo === 'receita' ? 'text-success' : 'text-ink-mute'
                }`}
              >
                {rascunho.tipo}
              </span>
              {rascunho.descricao}
            </span>
            <span className="font-display font-semibold tracking-tight text-ink">
              {rascunho.tipo === 'receita' ? '+' : '−'}
              {formatBRL(rascunho.valor)}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[12px] text-ink-soft mb-1">Conta</label>
              <select
                className="input"
                value={contaId}
                onChange={(e) => setContaId(e.target.value)}
              >
                <option value="">Escolha…</option>
                {contas.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[12px] text-ink-soft mb-1">Categoria</label>
              <select
                className="input"
                value={categoriaId}
                onChange={(e) => setCategoriaId(e.target.value)}
              >
                <option value="">Sem categoria</option>
                {categorias.map((c) => (
                  <option key={c.id} value={c.id}>
                    {`${'  '.repeat(c.depth)}${c.nome}`}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setRascunho(null)}
              className="btn-ghost px-4 py-2 text-sm"
            >
              Descartar
            </button>
            <button
              type="button"
              onClick={confirmar}
              disabled={salvando}
              className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
            >
              {salvando ? 'Lançando…' : 'Confirmar e lançar'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
