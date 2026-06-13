import { useState } from 'react';

import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';

/** Só renderiza em build de desenvolvimento (`next dev`). Em produção o bloco
 *  some no build e, por garantia, o endpoint responde 404. */
const EH_DEV = process.env.NODE_ENV !== 'production';

/**
 * Botão de dev: puxa os dados da PRODUÇÃO pro banco de DEV (one-way).
 * DESTRUTIVO — substitui o banco de dev inteiro. Pensado pra ter dados reais
 * pra testar sem mexer no terminal.
 */
export function DevSyncButton() {
  const [rodando, setRodando] = useState(false);
  const [msg, setMsg] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(
    null,
  );

  if (!EH_DEV) return null;

  async function sincronizar() {
    if (
      !window.confirm(
        'Copiar os dados da PRODUÇÃO para o dev?\n\n' +
          'Isto APAGA o banco de dev e o substitui pelo de produção. ' +
          'Seu login de dev continua o mesmo (a senha local é restaurada no fim). ' +
          'Não dá pra desfazer.',
      )
    ) {
      return;
    }
    setMsg(null);
    setRodando(true);
    try {
      const r = await api.devSyncProdToDev();
      setMsg({ tipo: 'ok', texto: r.mensagem });
      // Recarrega pra refletir os novos dados (e reautenticar se preciso).
      setTimeout(() => window.location.reload(), 1500);
    } catch (e) {
      setMsg({
        tipo: 'erro',
        texto: e instanceof ApiError ? e.message : 'Falha ao sincronizar.',
      });
    } finally {
      setRodando(false);
    }
  }

  return (
    <section className="mt-10 mb-4">
      <div className="card border-dashed p-4 flex flex-wrap items-center gap-3">
        <span className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute border border-line rounded px-1.5 py-0.5">
          dev
        </span>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-ink">
            Sincronizar dados da produção
          </div>
          <div className="text-[12px] text-ink-mute">
            Copia o banco de produção pro dev (substitui tudo). Só aparece em
            desenvolvimento.
          </div>
        </div>
        <button
          type="button"
          onClick={sincronizar}
          disabled={rodando}
          className="btn-ghost px-4 py-1.5 text-sm disabled:opacity-50"
        >
          {rodando ? 'Sincronizando…' : 'Puxar da produção'}
        </button>
      </div>
      {msg && (
        <div
          className={`mt-2 text-sm ${
            msg.tipo === 'ok' ? 'text-success-ink' : 'text-red-600'
          }`}
        >
          {msg.texto}
        </div>
      )}
    </section>
  );
}
