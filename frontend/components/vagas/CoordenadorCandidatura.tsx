import { useState } from 'react';

import { api } from '@/lib/api';
import type { CandidaturaAnalise, CandidaturaEntrega } from '@/lib/types';

type Fase = 'idle' | 'analisando' | 'checkpoint' | 'preparando' | 'pronto';

/**
 * Coordenador (MAS-2): cadeia "candidatura completa" com checkpoint humano.
 * Fase 1 analisa a vaga e PARA pra você decidir; Fase 2 (após o OK) gera CV +
 * carta + checklist. Cada passo é registrado na memória compartilhada (timeline
 * da vaga).
 */
export function CoordenadorCandidatura({
  vagaId,
  semPerfil,
  onMudou,
}: {
  vagaId: string;
  semPerfil: boolean;
  onMudou: () => void;
}) {
  const [fase, setFase] = useState<Fase>('idle');
  const [analise, setAnalise] = useState<CandidaturaAnalise | null>(null);
  const [entrega, setEntrega] = useState<CandidaturaEntrega | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  async function iniciar() {
    setErro(null);
    setFase('analisando');
    try {
      setAnalise(await api.candidaturaAnalisar(vagaId));
      setFase('checkpoint');
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao analisar.');
      setFase('idle');
    }
  }

  async function continuar() {
    setErro(null);
    setFase('preparando');
    try {
      setEntrega(await api.candidaturaPreparar(vagaId));
      setFase('pronto');
      onMudou();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao preparar.');
      setFase('checkpoint');
    }
  }

  function recomecar() {
    setFase('idle');
    setAnalise(null);
    setEntrega(null);
    setErro(null);
  }

  return (
    <div className="card p-4 border-brand/30 bg-brand-soft/20 mt-4">
      <div className="flex items-center justify-between gap-3 flex-wrap mb-1">
        <h4 className="font-display font-semibold text-sm text-ink m-0">
          🤝 Coordenador — candidatura completa
        </h4>
        {fase === 'idle' && (
          <button
            type="button"
            className="btn-primary disabled:opacity-40"
            onClick={iniciar}
            disabled={semPerfil}
          >
            Preparar candidatura
          </button>
        )}
        {(fase === 'pronto' || fase === 'checkpoint') && (
          <button type="button" className="btn-ghost" onClick={recomecar}>
            Recomeçar
          </button>
        )}
      </div>
      <p className="text-[12.5px] text-ink-soft m-0 mb-2">
        Analisa a vaga, você aprova, e ele encadeia CV + carta + checklist.
      </p>

      {erro && <p className="text-[13px] text-red-600 m-0 mb-2">{erro}</p>}

      {fase === 'analisando' && (
        <p className="text-[13px] text-ink-soft m-0">Analisando a vaga…</p>
      )}

      {fase === 'checkpoint' && analise && (
        <div className="rounded-lg border border-line bg-surface p-3.5">
          <div className="flex items-center gap-3 mb-2">
            <span className="font-display font-semibold text-2xl text-ink">
              {analise.aderencia}%
            </span>
            <span
              className={`text-[11px] px-2 py-0.5 rounded-full ${
                analise.recomenda
                  ? 'bg-green-100 text-green-700'
                  : 'bg-yellow-100 text-yellow-800'
              }`}
            >
              {analise.recomenda ? 'Vale aplicar' : 'Aderência baixa'}
            </span>
          </div>
          {analise.veredito && (
            <p className="text-[13px] text-ink m-0 mb-2">{analise.veredito}</p>
          )}
          {analise.gaps.length > 0 && (
            <div className="mb-2">
              <span className="text-[12px] text-ink-mute">Gaps: </span>
              <span className="text-[12.5px] text-ink">
                {analise.gaps.slice(0, 5).join(' · ')}
              </span>
            </div>
          )}
          <div className="flex items-center gap-2 mt-3">
            <button type="button" className="btn-primary" onClick={continuar}>
              Continuar → gerar CV + carta
            </button>
            <button type="button" className="btn-ghost" onClick={recomecar}>
              Cancelar
            </button>
          </div>
        </div>
      )}

      {fase === 'preparando' && (
        <p className="text-[13px] text-ink-soft m-0">
          Gerando CV sob medida, carta e checklist…
        </p>
      )}

      {fase === 'pronto' && entrega && (
        <div className="flex flex-col gap-3">
          <div className="rounded-lg border border-line bg-surface p-3.5">
            <h5 className="font-semibold text-[13px] text-ink m-0 mb-2">
              Checklist de entrega
            </h5>
            <ul className="flex flex-col gap-1 m-0 pl-4 text-[12.5px] text-ink-soft">
              {entrega.checklist.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </div>
          {entrega.email && (
            <details className="rounded-lg border border-line bg-surface p-3.5">
              <summary className="font-semibold text-[13px] text-ink cursor-pointer">
                E-mail{entrega.email.assunto ? `: ${entrega.email.assunto}` : ''}
              </summary>
              <pre className="text-[12.5px] text-ink-soft whitespace-pre-wrap font-sans mt-2 mb-0 leading-relaxed">
                {entrega.email.corpo}
              </pre>
            </details>
          )}
          {entrega.carta && (
            <details className="rounded-lg border border-line bg-surface p-3.5">
              <summary className="font-semibold text-[13px] text-ink cursor-pointer">
                Carta de apresentação
              </summary>
              <pre className="text-[12.5px] text-ink-soft whitespace-pre-wrap font-sans mt-2 mb-0 leading-relaxed">
                {entrega.carta.corpo}
              </pre>
            </details>
          )}
          <p className="text-[12px] text-ink-mute m-0">
            CV e carta também ficaram salvos na vaga (rascunhos). Revise antes de enviar.
          </p>
        </div>
      )}
    </div>
  );
}
