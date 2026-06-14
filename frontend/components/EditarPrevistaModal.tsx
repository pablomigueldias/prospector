import { useEffect, useRef, useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { useRecorrencias } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { type CategoriaPlana } from '@/lib/categorias';
import { formatBRL } from '@/lib/format';
import {
  ApiError,
  type Comprovante,
  type TransacaoResponse,
  type VerbaInput,
} from '@/lib/types';

/**
 * Editar uma conta **a pagar** (prevista) — detalhar/corrigir o que veio do
 * boleto sem mexer no saldo (ainda não foi paga): descrição, valor, categoria,
 * vencimento, encargos e as verbas (itens).
 */
export function EditarPrevistaModal({
  detalhe,
  categorias,
  onClose,
  onSaved,
}: {
  detalhe: TransacaoResponse;
  categorias: CategoriaPlana[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [descricao, setDescricao] = useState(detalhe.descricao);
  const [valor, setValor] = useState(String(detalhe.valor_total));
  const [vencimento, setVencimento] = useState(detalhe.data_vencimento ?? '');
  const [categoriaId, setCategoriaId] = useState(detalhe.categoria_id ?? '');
  const [recorrenciaId, setRecorrenciaId] = useState(detalhe.recorrencia_id ?? '');
  const { recorrencias } = useRecorrencias();
  const [multaPct, setMultaPct] = useState(
    detalhe.multa_percentual != null ? String(detalhe.multa_percentual) : '',
  );
  const [jurosPct, setJurosPct] = useState(
    detalhe.juros_mensal_percentual != null
      ? String(detalhe.juros_mensal_percentual)
      : '',
  );
  const [verbas, setVerbas] = useState<VerbaInput[]>(
    (detalhe.itens ?? []).map((i) => ({
      descricao: i.descricao,
      valor: String(i.valor),
    })),
  );
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  const somaVerbas = verbas.reduce(
    (acc, v) => acc + (Number(v.valor.replace(',', '.')) || 0),
    0,
  );
  const totalNum = Number(valor.replace(',', '.')) || 0;
  const verbasBatem = verbas.length === 0 || Math.abs(somaVerbas - totalNum) < 0.005;

  function setVerba(i: number, campo: keyof VerbaInput, v: string) {
    setVerbas((vs) => vs.map((x, idx) => (idx === i ? { ...x, [campo]: v } : x)));
  }
  function addVerba() {
    setVerbas((vs) => [...vs, { descricao: '', valor: '' }]);
  }
  function removerVerba(i: number) {
    setVerbas((vs) => vs.filter((_, idx) => idx !== i));
  }

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!descricao.trim()) return setErro('Descreva a conta.');
    if (!Number.isFinite(totalNum) || totalNum <= 0) {
      return setErro('Informe um valor maior que zero.');
    }
    const itens = verbas
      .filter((v) => v.descricao.trim() && Number(v.valor.replace(',', '.')) > 0)
      .map((v) => ({
        descricao: v.descricao.trim(),
        valor: String(Number(v.valor.replace(',', '.'))),
      }));

    setSalvando(true);
    try {
      await api.financasEditarPrevista(detalhe.id, {
        descricao: descricao.trim(),
        valor_total: String(totalNum),
        categoria_id: categoriaId || null,
        data_vencimento: vencimento || null,
        multa_percentual: multaPct !== '' ? multaPct : null,
        juros_mensal_percentual: jurosPct !== '' ? jurosPct : null,
        itens, // substitui as verbas (mesmo vazio limpa)
        recorrencia_id: recorrenciaId || null,
      });
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao salvar.');
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title="Editar conta a pagar" maxWidth="max-w-lg">
      <form onSubmit={salvar} className="space-y-4">
        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Descrição
          </label>
          <input
            className="input"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            autoFocus
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Valor total
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
              Vencimento
            </label>
            <input
              type="date"
              className="input"
              value={vencimento}
              onChange={(e) => setVencimento(e.target.value)}
            />
          </div>
        </div>

        <div className="grid grid-cols-[1fr_auto_auto] gap-3 items-end">
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
          <div className="w-20">
            <label className="block text-[12px] text-ink-soft mb-1">Multa %</label>
            <input
              className="input"
              value={multaPct}
              onChange={(e) => setMultaPct(e.target.value)}
              inputMode="decimal"
              placeholder="2"
            />
          </div>
          <div className="w-20">
            <label className="block text-[12px] text-ink-soft mb-1">Juros %/mês</label>
            <input
              className="input"
              value={jurosPct}
              onChange={(e) => setJurosPct(e.target.value)}
              inputMode="decimal"
              placeholder="1"
            />
          </div>
        </div>

        {/* Conta fixa (recorrência) à qual essa despesa pertence */}
        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Conta fixa (opcional)
          </label>
          <select
            className="input"
            value={recorrenciaId}
            onChange={(e) => setRecorrenciaId(e.target.value)}
          >
            <option value="">Não é conta fixa</option>
            {recorrencias.map((r) => (
              <option key={r.id} value={r.id}>
                {r.descricao}
              </option>
            ))}
          </select>
          <p className="text-[12px] text-ink-mute mt-1 m-0">
            Liga essa despesa a uma conta fixa (ex.: o boleto do aluguel) — conta
            como a do mês.
          </p>
        </div>

        {/* Editor de verbas (subitens do boleto) */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-[13px] font-medium text-ink-soft">
              Verbas (detalhamento)
            </label>
            <button
              type="button"
              onClick={addVerba}
              className="text-[12px] text-brand hover:underline"
            >
              + adicionar
            </button>
          </div>
          {verbas.length === 0 ? (
            <p className="text-[12px] text-ink-mute">
              Sem detalhamento. Adicione as verbas do boleto se quiser.
            </p>
          ) : (
            <div className="space-y-2">
              {verbas.map((v, i) => (
                <div key={i} className="flex gap-2">
                  <input
                    className="input flex-1"
                    value={v.descricao}
                    onChange={(e) => setVerba(i, 'descricao', e.target.value)}
                    placeholder="ex: Taxa de condomínio"
                  />
                  <input
                    className="input w-28"
                    value={v.valor}
                    onChange={(e) => setVerba(i, 'valor', e.target.value)}
                    inputMode="decimal"
                    placeholder="0,00"
                  />
                  <button
                    type="button"
                    onClick={() => removerVerba(i)}
                    className="text-ink-faint hover:text-red-600 px-1"
                    aria-label="Remover verba"
                  >
                    ✕
                  </button>
                </div>
              ))}
              <div
                className={`text-[12px] ${verbasBatem ? 'text-ink-mute' : 'text-amber-600'}`}
              >
                Soma das verbas: {formatBRL(somaVerbas)}
                {!verbasBatem && ` (difere do total ${formatBRL(totalNum)})`}
              </div>
            </div>
          )}
        </div>

        <AnexosTransacao transacaoId={detalhe.id} />

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
            {salvando ? 'Salvando…' : 'Salvar'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/** Comprovantes anexados à transação: lista (com link) + anexar novo arquivo. */
function AnexosTransacao({ transacaoId }: { transacaoId: string }) {
  const [itens, setItens] = useState<Comprovante[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function carregar() {
    try {
      const r = await api.financasComprovantesDaTransacao(transacaoId);
      setItens(r.items);
    } catch {
      /* ignora — anexos são opcionais */
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    void carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transacaoId]);

  async function anexar(file: File) {
    setEnviando(true);
    try {
      await api.financasAnexarComprovante(transacaoId, file);
      await carregar();
    } catch {
      /* ignora */
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-[13px] font-medium text-ink-soft">
          Comprovantes / anexos
        </label>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={enviando}
          className="text-[12px] text-brand hover:underline disabled:opacity-50"
        >
          {enviando ? 'enviando…' : '+ anexar'}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,image/*"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void anexar(f);
            e.target.value = '';
          }}
        />
      </div>
      {carregando ? (
        <p className="text-[12px] text-ink-mute">carregando…</p>
      ) : itens.length === 0 ? (
        <p className="text-[12px] text-ink-mute">
          Nenhum arquivo anexado. (boleto, recibo de pagamento…)
        </p>
      ) : (
        <ul className="space-y-1">
          {itens.map((c) => (
            <li key={c.id} className="text-[12.5px] flex items-center gap-1.5">
              <span aria-hidden>📎</span>
              {c.url ? (
                <a
                  href={c.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand hover:underline truncate"
                >
                  {c.nome_original || c.tipo}
                </a>
              ) : (
                <span className="text-ink-soft truncate">
                  {c.nome_original || c.tipo}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
