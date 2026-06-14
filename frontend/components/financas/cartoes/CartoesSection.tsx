import { useState } from 'react';

import { useCartoes, useProjecaoCartoes } from '@/hooks/useFinancas';
import type { Cartao } from '@/lib/types';

import { CartaoCard } from './CartaoCard';
import { CartaoForm } from './CartaoForm';
import { ProjecaoBlock } from './ProjecaoBlock';

type ModalState =
  | { modo: 'fechado' }
  | { modo: 'novo' }
  | { modo: 'editar'; cartao: Cartao };

export function CartoesSection() {
  const { cartoes, loading, refetch } = useCartoes();
  const [modal, setModal] = useState<ModalState>({ modo: 'fechado' });
  // Bumpa quando um card muda (compra/estorno/pagar) pra a projeção atualizar.
  const [mutacao, setMutacao] = useState(0);
  const bump = () => setMutacao((n) => n + 1);
  const { projecao } = useProjecaoCartoes(6, mutacao);

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Cartões
        </h2>
        <button
          type="button"
          onClick={() => setModal({ modo: 'novo' })}
          className="btn-ghost px-3.5 py-1.5 text-sm"
        >
          + Novo cartão
        </button>
      </div>

      {loading ? (
        <div className="card p-4 h-[120px] animate-pulse" />
      ) : cartoes.length === 0 ? (
        <div className="card p-6 text-center text-ink-soft text-sm">
          Nenhum cartão cadastrado. Clique em “Novo cartão” pra começar.
        </div>
      ) : (
        <>
          {projecao && projecao.meses.length > 0 && <ProjecaoBlock projecao={projecao} />}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {cartoes.map((c) => (
              <CartaoCard
                key={c.id}
                cartao={c}
                onEditar={() => setModal({ modo: 'editar', cartao: c })}
                onMutou={bump}
              />
            ))}
          </div>
        </>
      )}

      {modal.modo !== 'fechado' && (
        <CartaoForm
          cartao={modal.modo === 'editar' ? modal.cartao : null}
          onClose={() => setModal({ modo: 'fechado' })}
          onSaved={() => {
            setModal({ modo: 'fechado' });
            void refetch();
          }}
        />
      )}
    </section>
  );
}
