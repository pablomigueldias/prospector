import { type FreelaTaxaPorAnguloItem } from '@/lib/types';

// Rótulos dos ângulos (espelha o PropostaModal).
const ANGULO_LABEL: Record<string, string> = {
  direto: '🎯 Direto ao ponto',
  prova: '🏆 Abre com prova',
  pergunta: '❓ Abre com pergunta',
};

/**
 * "Qual abertura converte" — taxa de resposta por ângulo da 1ª linha (A/B, §2.F).
 * Mostra qual estilo de abertura (direto/prova/pergunta) faz o cliente responder
 * mais. Só aparece quando há propostas enviadas com ângulo marcado.
 */
export function QualAbertura({
  itens,
  loading,
}: {
  itens: FreelaTaxaPorAnguloItem[];
  loading: boolean;
}) {
  if (loading || itens.length === 0) return null;

  const max = Math.max(...itens.map((i) => i.taxa_resposta), 0.01);

  return (
    <section className="card p-5 mt-7">
      <h2 className="font-display font-semibold text-base tracking-tight text-ink m-0 mb-1">
        Qual abertura converte
      </h2>
      <p className="text-[13px] text-ink-soft mt-0 mb-4">
        Taxa de resposta por ângulo da 1ª linha — teste A/B de qual abre melhor a conversa.
      </p>
      <div className="flex flex-col gap-2.5">
        {itens.map((i) => (
          <div key={i.angulo} className="flex items-center gap-3 text-[13px]">
            <span className="w-40 shrink-0 truncate text-ink">
              {ANGULO_LABEL[i.angulo] ?? i.angulo}
            </span>
            <div className="flex-1 h-2 rounded-full bg-bg-alt overflow-hidden">
              <div
                className="h-full rounded-full bg-brand"
                style={{ width: `${(i.taxa_resposta / max) * 100}%` }}
              />
            </div>
            <span className="w-28 shrink-0 text-right tabular-nums text-ink-soft">
              {Math.round(i.taxa_resposta * 100)}%
              <span className="text-ink-faint">
                {' '}
                ({i.respondidas}/{i.enviadas})
              </span>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
