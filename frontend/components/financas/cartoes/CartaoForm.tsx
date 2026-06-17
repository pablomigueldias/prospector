import { useState, type FormEvent } from 'react';

import { Modal } from '@/components/shared/Modal';
import { api } from '@/lib/api';
import { ApiError, type Cartao } from '@/lib/types';

/** Modal de criar/editar (e excluir) um cartão. */
export function CartaoForm({
  cartao,
  onClose,
  onSaved,
}: {
  cartao: Cartao | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = cartao !== null;
  const [nome, setNome] = useState(cartao?.nome ?? '');
  const [bandeira, setBandeira] = useState(cartao?.bandeira ?? '');
  const [fechamento, setFechamento] = useState(String(cartao?.dia_fechamento ?? 1));
  const [vencimento, setVencimento] = useState(String(cartao?.dia_vencimento ?? 10));
  const [limite, setLimite] = useState(cartao?.limite ?? '');
  const [ativo, setAtivo] = useState(cartao?.ativo ?? true);
  const [salvando, setSalvando] = useState(false);
  const [excluindo, setExcluindo] = useState(false);
  const [erro, setErro] = useState('');

  function diaValido(s: string): number | null {
    const n = Number(s);
    return Number.isInteger(n) && n >= 1 && n <= 31 ? n : null;
  }

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!nome.trim()) return setErro('Dê um nome pro cartão.');
    const fech = diaValido(fechamento);
    const venc = diaValido(vencimento);
    if (fech === null) return setErro('Dia de fechamento entre 1 e 31.');
    if (venc === null) return setErro('Dia de vencimento entre 1 e 31.');
    const limiteStr = limite.trim()
      ? String(Number(limite.replace(',', '.')))
      : null;
    if (limiteStr !== null && !Number.isFinite(Number(limiteStr))) {
      return setErro('Limite inválido.');
    }

    setSalvando(true);
    try {
      if (editando && cartao) {
        await api.financasAtualizarCartao(cartao.id, {
          nome: nome.trim(),
          bandeira: bandeira.trim() || null,
          dia_fechamento: fech,
          dia_vencimento: venc,
          limite: limiteStr,
          ativo,
        });
      } else {
        await api.financasCriarCartao({
          nome: nome.trim(),
          bandeira: bandeira.trim() || null,
          dia_fechamento: fech,
          dia_vencimento: venc,
          limite: limiteStr,
        });
      }
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao salvar.');
    } finally {
      setSalvando(false);
    }
  }

  async function excluir() {
    if (!cartao) return;
    if (
      !window.confirm(
        `Excluir o cartão “${cartao.nome}”? As faturas dele são removidas junto. ` +
          'Compras parceladas continuam, sem o vínculo.',
      )
    ) {
      return;
    }
    setErro('');
    setExcluindo(true);
    try {
      await api.financasExcluirCartao(cartao.id);
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao excluir.');
      setExcluindo(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={editando ? 'Editar cartão' : 'Novo cartão'}>
      <form onSubmit={salvar} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Nome
            </label>
            <input
              className="input"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="ex: Nubank"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Bandeira (opcional)
            </label>
            <input
              className="input"
              value={bandeira}
              onChange={(e) => setBandeira(e.target.value)}
              placeholder="ex: Mastercard"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Fecha dia
            </label>
            <input
              className="input"
              value={fechamento}
              onChange={(e) => setFechamento(e.target.value)}
              inputMode="numeric"
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Vence dia
            </label>
            <input
              className="input"
              value={vencimento}
              onChange={(e) => setVencimento(e.target.value)}
              inputMode="numeric"
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Limite
            </label>
            <input
              className="input"
              value={limite}
              onChange={(e) => setLimite(e.target.value)}
              inputMode="decimal"
              placeholder="0,00"
            />
          </div>
        </div>

        {editando && (
          <label className="flex items-center gap-2 text-sm text-ink-soft">
            <input
              type="checkbox"
              checked={ativo}
              onChange={(e) => setAtivo(e.target.checked)}
            />
            Ativo
          </label>
        )}

        {erro && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
            {erro}
          </div>
        )}

        <div className="flex items-center justify-between gap-3 pt-1">
          {editando ? (
            <button
              type="button"
              onClick={excluir}
              disabled={salvando || excluindo}
              className="text-sm text-red-600 hover:underline disabled:opacity-50"
            >
              {excluindo ? 'Excluindo…' : 'Excluir'}
            </button>
          ) : (
            <span />
          )}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="btn-ghost px-4 py-2 text-sm"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={salvando || excluindo}
              className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
            >
              {salvando ? 'Salvando…' : editando ? 'Salvar' : 'Criar cartão'}
            </button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
