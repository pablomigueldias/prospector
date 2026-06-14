import { useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { api } from '@/lib/api';
import { type CategoriaPlana } from '@/lib/categorias';
import { ApiError, type Conta } from '@/lib/types';

import { type LancamentoInicial } from './types';

export function LancamentoForm({
  contas,
  categorias,
  inicial,
  onClose,
  onSaved,
}: {
  contas: Conta[];
  categorias: CategoriaPlana[];
  /** Quando presente, o form abre em modo EDIÇÃO (PATCH em vez de lançar). */
  inicial?: LancamentoInicial;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = !!inicial;
  const hojeIso = new Date().toISOString().slice(0, 10);
  const [tipo, setTipo] = useState<'despesa' | 'receita'>(
    inicial?.tipo ?? 'despesa',
  );
  const [descricao, setDescricao] = useState(inicial?.descricao ?? '');
  const [valor, setValor] = useState(inicial?.valor ?? '');
  const [contaId, setContaId] = useState(inicial?.contaId ?? contas[0]?.id ?? '');
  const [categoriaId, setCategoriaId] = useState(inicial?.categoriaId ?? '');
  const [data, setData] = useState(inicial?.data ?? hojeIso);
  const [prevista, setPrevista] = useState(inicial?.prevista ?? false);
  // Despesa dividida em N contas (ex.: metade VR, metade dinheiro). Só pra
  // despesa nova (edição de dividida não é suportada — orienta excluir/relançar).
  const [dividir, setDividir] = useState(false);
  // Modo automático: esgota o VR/VA e joga o resto no dinheiro (sem digitar
  // valores). Usa o endpoint /despesa/auto-split. Sempre paga.
  const [autoSplit, setAutoSplit] = useState(false);
  const [vrId, setVrId] = useState(contas[0]?.id ?? '');
  const [fallbackId, setFallbackId] = useState(contas[1]?.id ?? contas[0]?.id ?? '');
  const [pagamentos, setPagamentos] = useState<{ conta_id: string; valor: string }[]>([
    { conta_id: contas[0]?.id ?? '', valor: '' },
    { conta_id: contas[1]?.id ?? contas[0]?.id ?? '', valor: '' },
  ]);
  const podeDividir = !editando && tipo === 'despesa';
  const dividindo = podeDividir && dividir;
  const autoSplitAtivo = dividindo && autoSplit;

  // Colar PIX copia-e-cola → preenche descrição e valor.
  const [pixAberto, setPixAberto] = useState(false);
  const [pixCodigo, setPixCodigo] = useState('');
  const [pixErro, setPixErro] = useState('');
  const [lendoPix, setLendoPix] = useState(false);

  async function lerPix() {
    setPixErro('');
    if (!pixCodigo.trim()) return;
    setLendoPix(true);
    try {
      const r = await api.financasParsePix(pixCodigo.trim());
      if (r.beneficiario) setDescricao(r.beneficiario);
      if (r.valor) setValor(String(r.valor).replace('.', ','));
      setPixAberto(false);
      setPixCodigo('');
    } catch (err) {
      setPixErro(err instanceof ApiError ? err.message : 'Não consegui ler o PIX.');
    } finally {
      setLendoPix(false);
    }
  }
  const valorNumPreview = Number(valor.replace(',', '.')) || 0;
  const somaPagamentos = pagamentos.reduce(
    (acc, p) => acc + (Number(p.valor.replace(',', '.')) || 0),
    0,
  );
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  function setPagamento(i: number, campo: 'conta_id' | 'valor', v: string) {
    setPagamentos((ps) => ps.map((p, idx) => (idx === i ? { ...p, [campo]: v } : p)));
  }

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!descricao.trim()) return setErro('Descreva o lançamento.');
    const valorNum = Number(valor.replace(',', '.'));
    if (!Number.isFinite(valorNum) || valorNum <= 0) {
      return setErro('Informe um valor maior que zero.');
    }

    setSalvando(true);
    try {
      if (autoSplitAtivo) {
        if (!vrId || !fallbackId) {
          setSalvando(false);
          return setErro('Escolha a conta que esgota (VR) e a que cobre o resto.');
        }
        if (vrId === fallbackId) {
          setSalvando(false);
          return setErro('As contas de VR e do resto precisam ser diferentes.');
        }
        await api.financasLancarDespesaAutoSplit({
          descricao: descricao.trim(),
          valor_total: String(valorNum),
          conta_vr_id: vrId,
          conta_fallback_id: fallbackId,
          categoria_id: categoriaId || null,
          data_competencia: data || null,
        });
        onSaved();
        return;
      }

      if (dividindo) {
        const pags = pagamentos
          .filter((p) => p.conta_id && Number(p.valor.replace(',', '.')) > 0)
          .map((p) => ({ conta_id: p.conta_id, valor: String(Number(p.valor.replace(',', '.'))) }));
        if (pags.length < 2) {
          setSalvando(false);
          return setErro('Divida em pelo menos duas contas (ou desmarque a divisão).');
        }
        if (Math.abs(somaPagamentos - valorNum) >= 0.005) {
          setSalvando(false);
          return setErro(`A soma das contas (${somaPagamentos.toFixed(2)}) precisa bater com o total (${valorNum.toFixed(2)}).`);
        }
        await api.financasLancarDespesaDividida({
          descricao: descricao.trim(),
          valor_total: String(valorNum),
          pagamentos: pags,
          categoria_id: categoriaId || null,
          data_competencia: data || null,
          status: prevista ? 'prevista' : 'paga',
        });
        onSaved();
        return;
      }

      if (!contaId) {
        setSalvando(false);
        return setErro('Escolha a conta.');
      }
      const body = {
        descricao: descricao.trim(),
        valor_total: String(valorNum),
        conta_id: contaId,
        categoria_id: categoriaId || null,
        data_competencia: data || null,
        status: prevista ? ('prevista' as const) : ('paga' as const),
      };
      if (inicial) {
        await api.financasEditarTransacao(inicial.id, { tipo, ...body });
      } else if (tipo === 'despesa') {
        await api.financasLancarDespesa(body);
      } else {
        await api.financasLancarReceita(body);
      }
      onSaved();
    } catch (err) {
      const acao = editando ? 'salvar' : 'lançar';
      setErro(err instanceof ApiError ? err.message : `Falha ao ${acao}.`);
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={editando ? 'Editar lançamento' : 'Novo lançamento'}>
      <form onSubmit={salvar} className="space-y-4">
        {/* Toggle despesa / receita */}
        <div className="grid grid-cols-2 gap-2">
          {(['despesa', 'receita'] as const).map((t) => (
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
              {t === 'despesa' ? 'Despesa' : 'Receita'}
            </button>
          ))}
        </div>

        {/* Colar PIX → preenche descrição + valor */}
        {!editando && (
          <div>
            {!pixAberto ? (
              <button
                type="button"
                onClick={() => setPixAberto(true)}
                className="text-[12.5px] text-brand hover:underline"
              >
                📋 Colar código PIX
              </button>
            ) : (
              <div className="space-y-2 border border-line-soft rounded-lg p-3">
                <textarea
                  className="input min-h-[64px] font-mono text-[11px]"
                  value={pixCodigo}
                  onChange={(e) => setPixCodigo(e.target.value)}
                  placeholder="Cole aqui o PIX copia-e-cola…"
                  autoFocus
                />
                {pixErro && <div className="text-[12px] text-red-600">{pixErro}</div>}
                <div className="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setPixAberto(false);
                      setPixCodigo('');
                      setPixErro('');
                    }}
                    className="text-[12.5px] text-ink-mute hover:text-ink px-2"
                  >
                    cancelar
                  </button>
                  <button
                    type="button"
                    onClick={lerPix}
                    disabled={lendoPix || !pixCodigo.trim()}
                    className="btn-primary px-3 py-1 text-[12.5px] disabled:opacity-50"
                  >
                    {lendoPix ? 'Lendo…' : 'Preencher'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Descrição
          </label>
          <input
            className="input"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            placeholder={tipo === 'despesa' ? 'ex: Mercado' : 'ex: Salário'}
            autoFocus
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Valor
            </label>
            <input
              className="input"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
              inputMode="decimal"
              placeholder="0,00"
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Data
            </label>
            <input
              type="date"
              className="input"
              value={data}
              onChange={(e) => setData(e.target.value)}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              {dividindo
                ? 'Contas'
                : tipo === 'despesa'
                  ? 'Conta (saiu de)'
                  : 'Conta (entrou em)'}
            </label>
            {dividindo ? (
              <div className="input flex items-center text-ink-mute text-[13px]">
                dividida abaixo ↓
              </div>
            ) : (
              <select
                className="input"
                value={contaId}
                onChange={(e) => setContaId(e.target.value)}
              >
                {contas.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            )}
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Categoria
            </label>
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

        {podeDividir && (
          <label className="flex items-center gap-2 text-sm text-ink-soft">
            <input
              type="checkbox"
              checked={dividir}
              onChange={(e) => setDividir(e.target.checked)}
            />
            Dividir entre contas (ex.: metade VR, metade dinheiro)
          </label>
        )}

        {dividindo && (
          <div className="flex gap-2 text-[13px]">
            {([
              [false, 'Valores manuais'],
              [true, 'Auto (esgota o VR)'],
            ] as const).map(([modo, rotulo]) => (
              <button
                key={rotulo}
                type="button"
                onClick={() => setAutoSplit(modo)}
                className={`flex-1 py-1.5 rounded-lg border transition-colors ${
                  autoSplit === modo
                    ? 'border-brand bg-brand-soft text-brand-ink'
                    : 'border-line text-ink-soft hover:border-ink-mute'
                }`}
              >
                {rotulo}
              </button>
            ))}
          </div>
        )}

        {autoSplitAtivo && (
          <div className="space-y-2 border border-line-soft rounded-lg p-3">
            <p className="text-[12.5px] text-ink-mute m-0">
              Gasta o que tiver na 1ª conta (VR/VA) e joga o que faltar na 2ª.
              Lançado como pago.
            </p>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11.5px] text-ink-mute mb-1">
                  Esgota primeiro (VR/VA)
                </label>
                <select
                  className="input"
                  value={vrId}
                  onChange={(e) => setVrId(e.target.value)}
                >
                  <option value="">Conta…</option>
                  {contas.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11.5px] text-ink-mute mb-1">
                  Cobre o resto
                </label>
                <select
                  className="input"
                  value={fallbackId}
                  onChange={(e) => setFallbackId(e.target.value)}
                >
                  <option value="">Conta…</option>
                  {contas.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {dividindo && !autoSplit && (
          <div className="space-y-2 border border-line-soft rounded-lg p-3">
            {pagamentos.map((p, i) => (
              <div key={i} className="flex items-center gap-2">
                <select
                  className="input flex-1"
                  value={p.conta_id}
                  onChange={(e) => setPagamento(i, 'conta_id', e.target.value)}
                >
                  <option value="">Conta…</option>
                  {contas.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome}
                    </option>
                  ))}
                </select>
                <input
                  className="input w-28"
                  value={p.valor}
                  onChange={(e) => setPagamento(i, 'valor', e.target.value)}
                  inputMode="decimal"
                  placeholder="0,00"
                />
                {pagamentos.length > 2 && (
                  <button
                    type="button"
                    onClick={() => setPagamentos((ps) => ps.filter((_, idx) => idx !== i))}
                    className="text-ink-mute hover:text-red-600 text-lg leading-none px-1"
                    title="Remover"
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={() => setPagamentos((ps) => [...ps, { conta_id: '', valor: '' }])}
                className="text-[13px] text-brand hover:underline"
              >
                + conta
              </button>
              <span
                className={`text-[12.5px] tabular-nums ${
                  Math.abs(somaPagamentos - valorNumPreview) < 0.005
                    ? 'text-ink-mute'
                    : 'text-red-600'
                }`}
              >
                soma {somaPagamentos.toFixed(2)} / total {valorNumPreview.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        {!autoSplitAtivo && (
          <label className="flex items-center gap-2 text-sm text-ink-soft">
            <input
              type="checkbox"
              checked={prevista}
              onChange={(e) => setPrevista(e.target.checked)}
            />
            Lançar como prevista (não mexe no saldo ainda)
          </label>
        )}

        {erro && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
            {erro}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-1">
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost px-4 py-2 text-sm"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={salvando}
            className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
          >
            {salvando
              ? editando
                ? 'Salvando…'
                : 'Lançando…'
              : editando
                ? 'Salvar'
                : 'Lançar'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
