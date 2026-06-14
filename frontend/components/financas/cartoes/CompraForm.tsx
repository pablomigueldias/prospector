import { useMemo, useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { useCategorias } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias } from '@/lib/categorias';
import { formatBRL } from '@/lib/format';
import { ApiError, type Cartao } from '@/lib/types';

/** Modal de lançar compra (à vista ou parcelada) num cartão. */
export function CompraForm({
  cartao,
  onClose,
  onSaved,
}: {
  cartao: Cartao;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { arvore } = useCategorias();
  const categorias = useMemo(() => achatarCategorias(arvore), [arvore]);

  const [descricao, setDescricao] = useState('');
  const [valor, setValor] = useState('');
  const [parcelas, setParcelas] = useState('1');
  const [dataCompra, setDataCompra] = useState(
    () => new Date().toISOString().slice(0, 10),
  );
  const [categoriaId, setCategoriaId] = useState('');
  const [catReaproveitada, setCatReaproveitada] = useState('');
  const [comJuros, setComJuros] = useState(false);
  const [juros, setJuros] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  // Auto-categoria: ao sair do campo de descrição, se ainda não escolheu
  // categoria, reaproveita a da última compra com a mesma descrição.
  async function sugerirCategoria() {
    if (categoriaId || !descricao.trim()) return;
    try {
      const s = await api.financasSugestaoCategoriaCompra(descricao.trim());
      if (s.categoria_id) {
        setCategoriaId(s.categoria_id);
        setCatReaproveitada(s.categoria_nome ?? '');
      }
    } catch {
      /* sugestão é best-effort — ignora falha */
    }
  }

  const nParcelas = Number(parcelas);
  const valorNum = Number(valor.replace(',', '.'));
  const parcelaUnit =
    Number.isFinite(valorNum) && nParcelas >= 1 ? valorNum / nParcelas : 0;

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!descricao.trim()) return setErro('Descreva a compra.');
    if (!Number.isFinite(valorNum) || valorNum <= 0) {
      return setErro('Informe um valor maior que zero.');
    }
    if (!Number.isInteger(nParcelas) || nParcelas < 1 || nParcelas > 120) {
      return setErro('Número de parcelas entre 1 e 120.');
    }
    const jurosStr = comJuros && juros.trim()
      ? String(Number(juros.replace(',', '.')))
      : '0';
    if (!Number.isFinite(Number(jurosStr)) || Number(jurosStr) < 0) {
      return setErro('Juros inválido.');
    }
    if (Number(jurosStr) > valorNum) {
      return setErro('O juro não pode ser maior que o total.');
    }

    setSalvando(true);
    try {
      await api.financasCriarCompra({
        cartao_id: cartao.id,
        descricao: descricao.trim(),
        valor_total: String(valorNum),
        total_parcelas: nParcelas,
        data_compra: dataCompra || null,
        categoria_id: categoriaId || null,
        valor_juros_total: jurosStr,
      });
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao lançar a compra.');
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={`Compra no ${cartao.nome}`}>
      <form onSubmit={salvar} className="space-y-4">
        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Descrição
          </label>
          <input
            className="input"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            onBlur={sugerirCategoria}
            placeholder="ex: Geladeira"
            autoFocus
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
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
              Parcelas
            </label>
            <input
              className="input"
              value={parcelas}
              onChange={(e) => setParcelas(e.target.value)}
              inputMode="numeric"
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Data da compra
            </label>
            <input
              type="date"
              className="input"
              value={dataCompra}
              onChange={(e) => setDataCompra(e.target.value)}
            />
          </div>
        </div>

        {parcelaUnit > 0 && (
          <p className="text-[12.5px] text-ink-mute m-0">
            {nParcelas === 1
              ? `À vista — entra na próxima fatura: ${formatBRL(valorNum)}`
              : `${nParcelas}× de ${formatBRL(parcelaUnit)} (a última ajusta os centavos)`}
          </p>
        )}

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Categoria (opcional)
          </label>
          <select
            className="input"
            value={categoriaId}
            onChange={(e) => {
              setCategoriaId(e.target.value);
              setCatReaproveitada('');
            }}
          >
            <option value="">Sem categoria</option>
            {categorias.map((c) => (
              <option key={c.id} value={c.id}>
                {`${'  '.repeat(c.depth)}${c.nome}`}
              </option>
            ))}
          </select>
          {catReaproveitada && (
            <p className="text-[11.5px] text-ink-mute mt-1 m-0">
              categoria reaproveitada de uma compra parecida ({catReaproveitada})
            </p>
          )}
        </div>

        <div>
          <label className="flex items-center gap-2 text-sm text-ink-soft">
            <input
              type="checkbox"
              checked={comJuros}
              onChange={(e) => setComJuros(e.target.checked)}
            />
            Tem juros embutido
          </label>
          {comJuros && (
            <input
              className="input mt-2"
              value={juros}
              onChange={(e) => setJuros(e.target.value)}
              inputMode="decimal"
              placeholder="Quanto do total é juro (0,00)"
            />
          )}
        </div>

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
            {salvando ? 'Lançando…' : 'Lançar compra'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
