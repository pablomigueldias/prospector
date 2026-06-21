import { useState } from 'react';

import { CartaPdf } from '@/components/vagas/CartaPdf';
import { CoordenadorCandidatura } from '@/components/vagas/CoordenadorCandidatura';
import { CurriculoPdf } from '@/components/vagas/CurriculoPdf';
import { usePerfil } from '@/hooks/usePerfil';
import { useVaga, useVagaActions, useVagaRascunhos } from '@/hooks/useVagas';
import {
  type CandidaturaEmailItem,
  type ContatoPessoal,
  type CurriculoVaga,
  type GerarCandidaturaResponse,
  type Vaga,
  type VagaStatus,
} from '@/lib/types';
import { BlocoSalario, Campo, MatchPill, STATUS_LABEL, STATUS_ORDEM, Tags } from './_shared';

/**
 * Reconstrói o rascunho de candidatura a partir dos rascunhos salvos (a lista
 * vem newest-first). Junta o e-mail (+ variantes A/B) e a carta pra a tela não
 * "esquecer" o rascunho ao reabrir a vaga.
 */
function rascunhosParaCandidatura(
  rascunhos: CandidaturaEmailItem[],
): GerarCandidaturaResponse | null {
  const email = rascunhos.find((r) => r.tipo === 'email');
  const carta = rascunhos.find((r) => r.tipo === 'carta');
  if (!email && !carta) return null;
  return {
    success: true,
    email: email
      ? { assunto: email.assunto, corpo: email.corpo, tom: email.tom }
      : { corpo: '' },
    variantes_email: email?.variantes ?? [],
    carta: carta ? { corpo: carta.corpo, tom: carta.tom } : null,
    rascunho_id: email?.id ?? null,
  };
}

// ── Detalhe (detail) ──────────────────────────────────────────────

export function VagaDetalhe({
  vagaId,
  semPerfil,
  onMudou,
  onExcluida,
}: {
  vagaId: string;
  semPerfil: boolean;
  onMudou: () => void;
  onExcluida: () => void;
}) {
  const { vaga, loading, refetch } = useVaga(vagaId);
  const { perfil } = usePerfil();
  const { rascunhos, refetch: refetchRascunhos } = useVagaRascunhos(vagaId);
  const acoes = useVagaActions();
  const [candidatura, setCandidatura] = useState<GerarCandidaturaResponse | null>(
    null,
  );
  const [curriculo, setCurriculo] = useState<CurriculoVaga | null>(null);
  const [gerarCarta, setGerarCarta] = useState(true);
  const [aviso, setAviso] = useState<string | null>(null);
  const [editando, setEditando] = useState(false);

  // Currículo salvo na vaga (carrega ao reabrir); o recém-gerado tem prioridade.
  const curriculoMostrar = curriculo ?? vaga?.curriculo ?? null;
  // Rascunho de candidatura: o recém-gerado tem prioridade; senão reconstrói dos
  // rascunhos salvos (e-mail + variantes + carta) pra não sumir ao reabrir a vaga.
  const candidaturaMostrar = candidatura ?? rascunhosParaCandidatura(rascunhos);

  async function handleAnalisar() {
    setAviso(null);
    const r = await acoes.analisar(vagaId);
    if (r) {
      refetch();
      onMudou();
    }
  }

  async function handleGerar() {
    setAviso(null);
    const r = await acoes.gerarCandidatura(vagaId, gerarCarta);
    if (r) {
      setCandidatura(r);
      void refetchRascunhos();
      setAviso('Rascunho gerado. Revise antes de enviar — a ferramenta não envia.');
      onMudou();
    }
  }

  async function handleCurriculo() {
    setAviso(null);
    const r = await acoes.gerarCurriculo(vagaId);
    if (r) {
      setCurriculo(r.curriculo);
      refetch();
      onMudou();
    }
  }

  async function handleStatus(status: VagaStatus) {
    await acoes.atualizar(vagaId, { status });
    refetch();
    onMudou();
  }

  async function handleSalvarEdicao(body: Partial<Vaga>) {
    const r = await acoes.atualizar(vagaId, body);
    if (r) {
      setEditando(false);
      refetch();
      onMudou();
    }
  }

  async function handleExcluir() {
    if (!vaga) return;
    const ok = window.confirm(
      `Excluir a vaga "${vaga.titulo}"? Isso apaga análise, match, rascunhos e ` +
        'currículo salvo. Não dá pra desfazer.',
    );
    if (!ok) return;
    const r = await acoes.remover(vagaId);
    if (r !== null) onExcluida();
  }

  if (loading || !vaga) {
    return <div className="card p-8 h-64 animate-pulse" />;
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Cabeçalho da vaga */}
      {editando ? (
        <EditarVagaForm
          vaga={vaga}
          onSubmit={handleSalvarEdicao}
          onCancelar={() => setEditando(false)}
          loading={acoes.loading}
          erro={acoes.error?.message ?? null}
        />
      ) : (
        <div className="card p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-display font-semibold text-xl text-ink m-0">
                {vaga.titulo}
              </h3>
              <div className="text-[13px] text-ink-mute mt-1">
                {[vaga.empresa, vaga.modelo, vaga.localizacao]
                  .filter(Boolean)
                  .join(' · ') || '—'}
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {typeof vaga.match_score === 'number' && (
                <MatchPill score={vaga.match_score} grande />
              )}
              <button
                type="button"
                className="btn-ghost text-[12px] px-2 py-1"
                onClick={() => setEditando(true)}
                title="Editar os dados da vaga"
              >
                ✏️ Editar
              </button>
              <button
                type="button"
                className="text-[12px] px-2 py-1 text-red-600 hover:underline disabled:opacity-40"
                onClick={handleExcluir}
                disabled={acoes.loading}
                title="Excluir esta vaga"
              >
                🗑 Excluir
              </button>
            </div>
          </div>

          {vaga.link && (
            <a
              href={vaga.link}
              target="_blank"
              rel="noreferrer"
              className="inline-block mt-2 text-[12px] text-brand hover:underline truncate max-w-full"
            >
              {vaga.link}
            </a>
          )}

          {/* Status pipeline */}
          <div className="mt-4">
            <div className="text-[11px] font-medium text-ink-mute mb-1.5">
              Etapa — clique pra mover
            </div>
            <div className="flex flex-wrap gap-1.5">
              {STATUS_ORDEM.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => handleStatus(s)}
                  className={[
                    'font-mono text-[10px] uppercase tracking-[0.06em] px-2 py-1 rounded-sm transition-colors',
                    vaga.status === s
                      ? 'bg-brand text-white'
                      : 'bg-bg-alt text-ink-mute hover:text-ink',
                  ].join(' ')}
                >
                  {STATUS_LABEL[s]}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Ações de IA */}
      <div className="card p-5">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h4 className="font-display font-semibold text-sm text-ink m-0">
            Análise & candidatura
          </h4>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="btn-ghost disabled:opacity-40"
              onClick={handleAnalisar}
              disabled={acoes.loading || semPerfil}
            >
              {acoes.loading ? 'Processando…' : vaga.analise_json ? 'Reanalisar' : 'Analisar vaga'}
            </button>
            <label className="flex items-center gap-1.5 text-[12px] text-ink-soft">
              <input
                type="checkbox"
                checked={gerarCarta}
                onChange={(e) => setGerarCarta(e.target.checked)}
              />
              carta
            </label>
            <button
              type="button"
              className="btn-primary disabled:opacity-40"
              onClick={handleGerar}
              disabled={acoes.loading || semPerfil}
            >
              {acoes.loading ? 'Gerando…' : 'Gerar candidatura'}
            </button>
            <button
              type="button"
              className="btn-ghost disabled:opacity-40"
              onClick={handleCurriculo}
              disabled={acoes.loading || semPerfil}
            >
              {acoes.loading
                ? 'Gerando…'
                : curriculoMostrar
                  ? 'Regerar currículo'
                  : 'Gerar currículo'}
            </button>
          </div>
        </div>

        <CoordenadorCandidatura
          vagaId={vagaId}
          semPerfil={semPerfil}
          empresa={vaga.empresa}
          vagaTitulo={vaga.titulo}
          onMudou={() => {
            void refetch();
            onMudou();
          }}
        />

        {semPerfil && (
          <p className="text-[12px] text-ink-mute mt-3">
            Crie o Perfil Mestre pra habilitar a análise e a candidatura.
          </p>
        )}
        {aviso && (
          <div className="mt-3 text-[13px] text-ink-soft bg-bg-alt border border-line rounded p-3">
            {aviso}
          </div>
        )}
        {acoes.error && (
          <div className="mt-3 text-[13px] text-brand-ink bg-brand-soft/60 border border-brand/30 rounded p-3">
            {acoes.error.message}
          </div>
        )}
      </div>

      {/* Resultado da análise */}
      {vaga.analise_json && (
        <div className="card p-5">
          <h4 className="font-display font-semibold text-sm text-ink mb-3">
            O que a vaga exige
          </h4>
          {vaga.analise_json.resumo && (
            <p className="text-[13px] text-ink-soft mb-3">
              {vaga.analise_json.resumo}
            </p>
          )}
          <Tags titulo="Obrigatórios" itens={vaga.analise_json.requisitos_obrigatorios} forte />
          <Tags titulo="Desejáveis" itens={vaga.analise_json.desejaveis} />
          <Tags titulo="Stack" itens={vaga.analise_json.stack} />

          {vaga.analise_json.salario && (
            <BlocoSalario salario={vaga.analise_json.salario} />
          )}

          {vaga.match_json && (
            <div className="mt-4 pt-4 border-t border-line">
              <div className="flex items-center gap-2 mb-2">
                <h4 className="font-display font-semibold text-sm text-ink m-0">
                  Seu match
                </h4>
                <MatchPill score={vaga.match_json.aderencia} />
              </div>
              {vaga.match_json.veredito && (
                <p className="text-[13px] text-ink-soft mb-3">
                  {vaga.match_json.veredito}
                </p>
              )}
              <Tags titulo="Você tem" itens={vaga.match_json.tenho} ok />
              <Tags titulo="Gaps" itens={vaga.match_json.gaps} />
              <Tags titulo="Destacar" itens={vaga.match_json.destaques} />
              {vaga.match_json.plano_gaps && vaga.match_json.plano_gaps.length > 0 && (
                <div className="mt-1">
                  <div className="text-[12px] font-medium text-ink-mute mb-1.5">
                    🎯 Plano pros gaps (o que fazer)
                  </div>
                  <ul className="flex flex-col gap-1.5">
                    {vaga.match_json.plano_gaps.map((p, i) => (
                      <li
                        key={i}
                        className="text-[13px] text-ink-soft border border-line rounded p-2 bg-bg-alt/50"
                      >
                        <span className="text-ink font-medium">{p.gap}</span> → {p.acao}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Currículo ATS gerado (salvo na vaga; não regera ao reabrir) */}
      {curriculoMostrar && (
        <div>
          {vaga.curriculo_gerado_em && !curriculo && (
            <p className="text-[12px] text-ink-mute mb-2">
              Currículo salvo · gerado em{' '}
              {new Date(vaga.curriculo_gerado_em).toLocaleString('pt-BR')}. Use
              “Regerar” pra atualizar.
            </p>
          )}
          <CurriculoPdf curriculo={curriculoMostrar} vagaTitulo={vaga.titulo} />
        </div>
      )}

      {/* Rascunho gerado */}
      {candidaturaMostrar && (
        <RascunhoCandidatura
          dados={candidaturaMostrar}
          nome={curriculoMostrar?.nome ?? perfil?.nome ?? ''}
          contato={curriculoMostrar?.contato ?? perfil?.contato ?? null}
          empresa={vaga.empresa}
          vagaTitulo={vaga.titulo}
        />
      )}
    </div>
  );
}

function RascunhoCandidatura({
  dados,
  nome,
  contato,
  empresa,
  vagaTitulo,
}: {
  dados: GerarCandidaturaResponse;
  nome: string;
  contato?: ContatoPessoal | null;
  empresa?: string | null;
  vagaTitulo?: string | null;
}) {
  return (
    <div className="card p-5">
      <h4 className="font-display font-semibold text-sm text-ink mb-3">
        Rascunho — revise e envie você mesmo
      </h4>

      <BlocoTexto
        rotulo="E-mail"
        assunto={dados.email.assunto}
        corpo={dados.email.corpo}
      />

      {dados.variantes_email.map((v, i) => (
        <BlocoTexto
          key={i}
          rotulo={`Variante ${i + 1}`}
          assunto={v.assunto}
          corpo={v.corpo}
        />
      ))}

      {dados.carta && (
        <div className="mt-3">
          <CartaPdf
            carta={dados.carta}
            nome={nome}
            contato={contato}
            empresa={empresa}
            vagaTitulo={vagaTitulo}
          />
        </div>
      )}
    </div>
  );
}

function BlocoTexto({
  rotulo,
  assunto,
  corpo,
}: {
  rotulo: string;
  assunto?: string | null;
  corpo: string;
}) {
  const [copiado, setCopiado] = useState(false);

  function copiar() {
    const texto = assunto ? `Assunto: ${assunto}\n\n${corpo}` : corpo;
    navigator.clipboard.writeText(texto).then(() => {
      setCopiado(true);
      setTimeout(() => setCopiado(false), 1500);
    });
  }

  return (
    <div className="mb-4 last:mb-0">
      <div className="flex items-center justify-between mb-1.5">
        <span className="eyebrow">{rotulo}</span>
        <button
          type="button"
          className="text-[12px] text-brand hover:underline"
          onClick={copiar}
        >
          {copiado ? 'copiado!' : 'copiar'}
        </button>
      </div>
      {assunto && (
        <div className="text-[13px] font-medium text-ink mb-1">{assunto}</div>
      )}
      <pre className="text-[13px] text-ink-soft whitespace-pre-wrap font-sans bg-bg-alt border border-line rounded p-3 m-0">
        {corpo}
      </pre>
    </div>
  );
}


// ── Form de edição da vaga ────────────────────────────────────────

type CamposEditaveis = Pick<
  Vaga,
  | 'titulo'
  | 'empresa'
  | 'link'
  | 'fonte'
  | 'contato_nome'
  | 'contato_email'
  | 'localizacao'
  | 'modelo'
  | 'senioridade'
  | 'descricao'
  | 'notas'
>;

function EditarVagaForm({
  vaga,
  onSubmit,
  onCancelar,
  loading,
  erro,
}: {
  vaga: Vaga;
  onSubmit: (body: Partial<Vaga>) => void;
  onCancelar: () => void;
  loading: boolean;
  erro: string | null;
}) {
  const [f, setF] = useState<CamposEditaveis>({
    titulo: vaga.titulo,
    empresa: vaga.empresa ?? '',
    link: vaga.link ?? '',
    fonte: vaga.fonte ?? '',
    contato_nome: vaga.contato_nome ?? '',
    contato_email: vaga.contato_email ?? '',
    localizacao: vaga.localizacao ?? '',
    modelo: vaga.modelo ?? '',
    senioridade: vaga.senioridade ?? '',
    descricao: vaga.descricao,
    notas: vaga.notas ?? '',
  });

  function set<K extends keyof CamposEditaveis>(k: K, v: string) {
    setF((prev) => ({ ...prev, [k]: v }));
  }

  return (
    <div className="card p-6">
      <h4 className="font-display font-semibold text-sm text-ink mb-4">
        Editar vaga
      </h4>
      {erro && (
        <div className="text-[13px] text-brand-ink bg-brand-soft/60 border border-brand/30 rounded p-3 mb-4">
          {erro}
        </div>
      )}
      <div className="grid md:grid-cols-2 gap-4">
        <Campo label="Título da vaga" obrigatorio>
          <input className="input" value={f.titulo}
            onChange={(e) => set('titulo', e.target.value)} />
        </Campo>
        <Campo label="Empresa">
          <input className="input" value={f.empresa ?? ''}
            onChange={(e) => set('empresa', e.target.value)} />
        </Campo>
        <Campo label="Link da vaga">
          <input className="input" value={f.link ?? ''}
            onChange={(e) => set('link', e.target.value)} />
        </Campo>
        <Campo label="Fonte (LinkedIn, Gupy…)">
          <input className="input" value={f.fonte ?? ''}
            onChange={(e) => set('fonte', e.target.value)} />
        </Campo>
        <Campo label="Nome do contato">
          <input className="input" value={f.contato_nome ?? ''}
            onChange={(e) => set('contato_nome', e.target.value)} />
        </Campo>
        <Campo label="E-mail de contato">
          <input className="input" value={f.contato_email ?? ''}
            onChange={(e) => set('contato_email', e.target.value)} />
        </Campo>
        <Campo label="Localização">
          <input className="input" value={f.localizacao ?? ''}
            onChange={(e) => set('localizacao', e.target.value)} />
        </Campo>
        <Campo label="Modelo (remoto/híbrido/presencial)">
          <input className="input" value={f.modelo ?? ''}
            onChange={(e) => set('modelo', e.target.value)} />
        </Campo>
        <Campo label="Senioridade">
          <input className="input" value={f.senioridade ?? ''}
            onChange={(e) => set('senioridade', e.target.value)} />
        </Campo>
      </div>
      <div className="mt-4">
        <Campo label="Descrição da vaga" obrigatorio>
          <textarea className="input resize-y min-h-[140px]" value={f.descricao}
            onChange={(e) => set('descricao', e.target.value)} />
        </Campo>
      </div>
      <div className="mt-4">
        <Campo label="Notas (suas anotações)">
          <textarea className="input resize-y min-h-[70px]" value={f.notas ?? ''}
            onChange={(e) => set('notas', e.target.value)} />
        </Campo>
      </div>
      <div className="flex justify-end gap-2 mt-4">
        <button type="button" className="btn-ghost" onClick={onCancelar}
          disabled={loading}>
          Cancelar
        </button>
        <button
          type="button"
          className="btn-primary disabled:opacity-40"
          onClick={() => onSubmit(f)}
          disabled={loading || !f.titulo.trim() || !f.descricao.trim()}
        >
          {loading ? 'Salvando…' : 'Salvar alterações'}
        </button>
      </div>
    </div>
  );
}

