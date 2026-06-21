import { useState } from 'react';

import { type EstudoVagas, type SkillEstudo } from '@/lib/types';

// ── Painel de estudo (o que a maioria das vagas pede e você não tem) ──

export function PainelEstudo({
  estudo,
  loading,
}: {
  estudo: EstudoVagas | null | undefined;
  loading: boolean;
}) {
  const [expandido, setExpandido] = useState(false);

  if (loading && !estudo) {
    return (
      <div className="card p-5 mb-7 text-sm text-ink-mute">Montando sua lista de estudo…</div>
    );
  }
  if (!estudo || estudo.total_vagas === 0) {
    return (
      <div className="card p-5 mb-7">
        <h2 className="font-display font-semibold text-base text-ink m-0 mb-1">
          📚 O que estudar
        </h2>
        <p className="text-[13px] text-ink-soft m-0">
          Analise algumas vagas (botão <strong>Analisar</strong> em cada uma) que eu agrego
          aqui o que a maioria pede e você ainda não tem.
        </p>
      </div>
    );
  }

  const LIMITE = 12;
  const lista = expandido ? estudo.para_estudar : estudo.para_estudar.slice(0, LIMITE);
  const maxN = estudo.para_estudar[0]?.n_vagas || 1;

  return (
    <div className="card p-5 mb-7">
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-1">
        <h2 className="font-display font-semibold text-base text-ink m-0">
          📚 O que estudar — pedido pela maioria das vagas
        </h2>
        <span className="text-[12px] text-ink-faint">
          base: {estudo.total_vagas} vaga(s) analisada(s)
        </span>
      </div>
      <p className="text-[12px] text-ink-soft m-0 mb-3">
        Skills que aparecem nas vagas e <strong>não estão no seu perfil</strong> — quanto mais
        pra cima, mais a maioria pede. Foque do topo pra baixo.
      </p>

      {estudo.para_estudar.length === 0 ? (
        <p className="text-[13px] text-emerald-700 m-0">
          🎉 Você cobre todas as skills pedidas pelas vagas analisadas. Mire vagas mais
          sênior pra puxar a régua.
        </p>
      ) : (
        <ul className="m-0 p-0 list-none flex flex-col gap-1.5">
          {lista.map((s) => (
            <li key={s.skill} className="flex items-center gap-3">
              <span className="text-[13px] text-ink w-40 shrink-0 truncate" title={s.skill}>
                {s.skill}
              </span>
              <div className="flex-1 h-2 rounded-full bg-bg-alt overflow-hidden">
                <div
                  className="h-full bg-brand"
                  style={{ width: `${Math.round((s.n_vagas / maxN) * 100)}%` }}
                />
              </div>
              <span className="text-[12px] text-ink-soft w-28 shrink-0 text-right tabular-nums">
                {s.n_vagas} ({s.pct_vagas}%)
              </span>
              {s.obrigatoria_em > 0 ? (
                <span
                  className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 shrink-0"
                  title={`É requisito obrigatório em ${s.obrigatoria_em} vaga(s)`}
                >
                  obrig. {s.obrigatoria_em}
                </span>
              ) : (
                <span className="w-[58px] shrink-0" />
              )}
            </li>
          ))}
        </ul>
      )}

      {estudo.para_estudar.length > LIMITE && (
        <button
          type="button"
          className="btn-ghost text-[12px] mt-2"
          onClick={() => setExpandido((v) => !v)}
        >
          {expandido ? 'Mostrar menos' : `Ver todas (${estudo.para_estudar.length})`}
        </button>
      )}

      {estudo.pontos_fortes.length > 0 && (
        <div className="mt-4 pt-3 border-t border-line">
          <span className="text-[12px] font-medium text-emerald-700">
            ✅ Seus pontos fortes mais pedidos (destaque no currículo):
          </span>
          <div className="flex flex-wrap gap-1 mt-1.5">
            {estudo.pontos_fortes.map((s: SkillEstudo) => (
              <span
                key={s.skill}
                className="text-[12px] px-2 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200"
                title={`Pedido em ${s.n_vagas} vaga(s)`}
              >
                {s.skill} · {s.n_vagas}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

