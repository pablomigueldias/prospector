import { useState } from 'react';

import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import type { FreelaPropostaAnalise, FreelaPropostaEntrega } from '@/lib/types';

type Fase = 'idle' | 'analisando' | 'checkpoint' | 'preparando' | 'pronto';

const ANGULO_LABEL: Record<string, string> = {
  direto: '🎯 Direto',
  prova: '🏆 Prova',
  pergunta: '❓ Pergunta',
};

/**
 * Coordenador do freela (cadeia "proposta de freela"): analisa o projeto e PARA
 * num checkpoint (vale gastar proposta aqui?); ao aprovar, encadeia cotação +
 * redação + checklist. Cada passo é gravado na memória compartilhada (timeline
 * do projeto). Espelha o CoordenadorCandidatura.
 */
export function CoordenadorProposta({
  projetoId,
  onMudou,
}: {
  projetoId: string;
  onMudou: () => void;
}) {
  const [fase, setFase] = useState<Fase>('idle');
  const [analise, setAnalise] = useState<FreelaPropostaAnalise | null>(null);
  const [entrega, setEntrega] = useState<FreelaPropostaEntrega | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  async function iniciar() {
    setErro(null);
    setFase('analisando');
    try {
      setAnalise(await api.freelaCoordenadorAnalisar(projetoId));
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
      setEntrega(await api.freelaCoordenadorPreparar(projetoId));
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
          🤝 Coordenador — proposta completa
        </h4>
        {fase === 'idle' && (
          <button type="button" className="btn-primary" onClick={iniciar}>
            Preparar proposta
          </button>
        )}
        {(fase === 'pronto' || fase === 'checkpoint') && (
          <button type="button" className="btn-ghost" onClick={recomecar}>
            Recomeçar
          </button>
        )}
      </div>
      <p className="text-[12.5px] text-ink-soft m-0 mb-2">
        Analisa o projeto, você decide se vale gastar a proposta, e ele encadeia
        cotação + rascunho + checklist.
      </p>

      {erro && <p className="text-[13px] text-red-600 m-0 mb-2">{erro}</p>}

      {fase === 'analisando' && (
        <p className="text-[13px] text-ink-soft m-0">Analisando o projeto…</p>
      )}

      {fase === 'checkpoint' && analise && (
        <div className="rounded-lg border border-line bg-surface p-3.5">
          <div className="flex items-center gap-3 mb-2">
            <span className="font-display font-semibold text-2xl text-ink">
              {analise.fit_score}%
            </span>
            <span
              className={`text-[11px] px-2 py-0.5 rounded-full ${
                analise.recomenda
                  ? 'bg-green-100 text-green-700'
                  : 'bg-yellow-100 text-yellow-800'
              }`}
            >
              {analise.recomenda ? 'Vale a proposta' : 'Pense bem'}
            </span>
            {analise.risco && analise.risco !== 'baixo' && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-red-100 text-red-700">
                ⚠️ risco {analise.risco}
              </span>
            )}
          </div>
          {analise.veredito && (
            <p className="text-[13px] text-ink m-0 mb-2">{analise.veredito}</p>
          )}
          {analise.veredito_preco?.gap_texto && (
            <p className="text-[12.5px] text-ink-soft m-0 mb-2">
              💰 {analise.veredito_preco.gap_texto}
            </p>
          )}
          {analise.skills_faltando.length > 0 && (
            <div className="mb-2">
              <span className="text-[12px] text-ink-mute">Gaps de skill: </span>
              <span className="text-[12.5px] text-ink">
                {analise.skills_faltando.slice(0, 5).join(' · ')}
              </span>
            </div>
          )}
          {analise.perguntas_cliente.length > 0 && (
            <div className="mb-2">
              <span className="text-[12px] text-sky-700">Perguntar antes de cotar: </span>
              <span className="text-[12.5px] text-ink-soft">
                {analise.perguntas_cliente.slice(0, 3).join(' · ')}
              </span>
            </div>
          )}
          <div className="flex items-center gap-2 mt-3">
            <button type="button" className="btn-primary" onClick={continuar}>
              Continuar → cotar + redigir
            </button>
            <button type="button" className="btn-ghost" onClick={recomecar}>
              Cancelar
            </button>
          </div>
        </div>
      )}

      {fase === 'preparando' && (
        <p className="text-[13px] text-ink-soft m-0">
          Cotando, redigindo e conferindo a proposta…
        </p>
      )}

      {fase === 'pronto' && entrega && (
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-3 text-[13px]">
            {entrega.valor_cotado != null && (
              <span className="text-ink">
                Cotar <strong>{formatBRL(entrega.valor_cotado)}</strong>
              </span>
            )}
            {entrega.horas_estimadas != null && (
              <span className="text-ink-soft">{entrega.horas_estimadas}h</span>
            )}
            {entrega.prazo && <span className="text-ink-soft">{entrega.prazo}</span>}
            <span
              className={`text-[11px] px-2 py-0.5 rounded-full ${
                entrega.checklist_score >= 70
                  ? 'bg-green-100 text-green-700'
                  : 'bg-yellow-100 text-yellow-800'
              }`}
            >
              checklist {entrega.checklist_score}/100
              {entrega.checklist_selo ? ` · ${entrega.checklist_selo}` : ''}
            </span>
          </div>

          {entrega.texto && (
            <details className="rounded-lg border border-line bg-surface p-3.5" open>
              <summary className="font-semibold text-[13px] text-ink cursor-pointer">
                Rascunho da proposta
              </summary>
              <pre className="text-[12.5px] text-ink-soft whitespace-pre-wrap font-sans mt-2 mb-0 leading-relaxed">
                {entrega.texto}
              </pre>
            </details>
          )}

          {entrega.variacoes_abertura.length > 0 && (
            <div className="rounded-lg border border-line bg-surface p-3.5">
              <span className="font-semibold text-[13px] text-ink">
                Aberturas alternativas (A/B)
              </span>
              <ul className="flex flex-col gap-1.5 m-0 mt-2 p-0 list-none">
                {entrega.variacoes_abertura.map((v, i) => (
                  <li key={i} className="text-[12.5px] text-ink-soft">
                    <span className="text-[11px] text-ink-mute mr-1">
                      {ANGULO_LABEL[v.angulo] ?? v.angulo}
                    </span>
                    {v.texto}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {entrega.checklist_sugestoes.length > 0 && (
            <div className="rounded-lg border border-line bg-surface p-3.5">
              <span className="font-semibold text-[13px] text-amber-700">
                Antes de enviar
              </span>
              <ul className="flex flex-col gap-1 m-0 mt-1.5 pl-4 text-[12.5px] text-ink-soft">
                {entrega.checklist_sugestoes.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-[12px] text-ink-mute m-0">
            A proposta ficou salva no Kanban (rascunho). Abra o card pra ajustar e
            enviar na mão.
          </p>
        </div>
      )}
    </div>
  );
}
