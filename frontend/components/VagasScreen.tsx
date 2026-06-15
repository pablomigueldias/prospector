import { useState } from 'react';

import { CurriculoPdf } from './CurriculoPdf';
import { StatCard } from './StatCard';
import { usePerfil } from '@/hooks/usePerfil';
import { useVaga, useVagaActions, useVagas } from '@/hooks/useVagas';
import type {
  CurriculoVaga,
  GerarCandidaturaResponse,
  VagaCreate,
  VagaListItem,
  VagaStatus,
} from '@/lib/types';

const STATUS_LABEL: Record<VagaStatus, string> = {
  quero_candidatar: 'Quero candidatar',
  candidatei: 'Candidatei',
  respondeu: 'Respondeu',
  entrevista: 'Entrevista',
  fim: 'Encerrada',
};

const STATUS_ORDEM: VagaStatus[] = [
  'quero_candidatar',
  'candidatei',
  'respondeu',
  'entrevista',
  'fim',
];

export default function VagasScreen() {
  const vagas = useVagas();
  const { perfil } = usePerfil();
  const acoes = useVagaActions();
  const [selecionada, setSelecionada] = useState<string | null>(null);
  const [mostrarForm, setMostrarForm] = useState(false);

  const semPerfil = perfil === null;

  async function handleCriar(body: VagaCreate) {
    const v = await acoes.criar(body);
    if (v) {
      setMostrarForm(false);
      vagas.refetch();
      setSelecionada(v.id);
    }
  }

  const stats = computeStats(vagas.items);

  return (
    <div className="max-w-[1200px] mx-auto pb-16">
      <header className="mb-7">
        <div className="eyebrow mb-3">Pessoal · Caçador de vagas</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Vagas
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[62ch] leading-relaxed m-0">
          Cola a descrição da vaga, deixa a IA destrinchar o que ela exige,
          mede seu match e rascunha o e-mail de candidatura no seu tom. A
          ferramenta PARA no rascunho — você revisa e envia.
        </p>
      </header>

      {semPerfil && (
        <div className="mb-6 text-[13px] text-brand-ink bg-brand-soft/60 border border-brand/30 rounded p-3">
          Você ainda não tem um <strong>Perfil Mestre</strong>. Pode registrar
          vagas, mas a análise e a geração de candidatura precisam dele — crie o
          perfil primeiro.
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
        <StatCard label="Vagas" value={vagas.total} loading={vagas.loading} />
        <StatCard label="Quero candidatar" value={stats.quero_candidatar} loading={vagas.loading} />
        <StatCard label="Candidatei" value={stats.candidatei} loading={vagas.loading} />
        <StatCard label="Em processo" value={stats.emProcesso} loading={vagas.loading} />
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Suas vagas
        </h2>
        <button
          type="button"
          className="btn-primary"
          onClick={() => setMostrarForm((v) => !v)}
        >
          {mostrarForm ? 'Fechar' : '+ Nova vaga'}
        </button>
      </div>

      {mostrarForm && (
        <NovaVagaForm
          onSubmit={handleCriar}
          loading={acoes.loading}
          erro={acoes.error?.message ?? null}
        />
      )}

      <div className="grid md:grid-cols-[340px_1fr] gap-5 mt-2">
        <ListaVagas
          items={vagas.items}
          loading={vagas.loading}
          selecionada={selecionada}
          onSelecionar={setSelecionada}
        />
        <div>
          {selecionada ? (
            <VagaDetalhe
              key={selecionada}
              vagaId={selecionada}
              semPerfil={semPerfil}
              onMudou={() => vagas.refetch()}
            />
          ) : (
            <div className="card p-8 text-center text-sm text-ink-mute">
              Selecione uma vaga pra ver a análise e gerar a candidatura.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Lista (master) ────────────────────────────────────────────────

function ListaVagas({
  items,
  loading,
  selecionada,
  onSelecionar,
}: {
  items: VagaListItem[];
  loading: boolean;
  selecionada: string | null;
  onSelecionar: (id: string) => void;
}) {
  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card p-4 h-[72px] animate-pulse" />
        ))}
      </div>
    );
  }
  if (items.length === 0) {
    return (
      <div className="card p-6 text-center text-sm text-ink-mute">
        Nenhuma vaga ainda. Clique em "Nova vaga".
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {items.map((v) => {
        const ativa = v.id === selecionada;
        return (
          <button
            key={v.id}
            type="button"
            onClick={() => onSelecionar(v.id)}
            className={[
              'card p-3.5 text-left transition-colors',
              ativa ? 'border-brand ring-1 ring-brand/30' : 'hover:border-line-strong',
            ].join(' ')}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-sm font-medium text-ink leading-snug">
                {v.titulo}
              </span>
              {typeof v.match_score === 'number' && (
                <MatchPill score={v.match_score} />
              )}
            </div>
            <div className="text-[12px] text-ink-mute mt-0.5">
              {v.empresa || 'sem empresa'}
            </div>
            <div className="flex items-center gap-2 mt-2">
              <StatusBadge status={v.status} />
              {v.qtd_rascunhos > 0 && (
                <span className="font-mono text-[10px] text-ink-mute">
                  {v.qtd_rascunhos} rascunho(s)
                </span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}

// ── Detalhe (detail) ──────────────────────────────────────────────

function VagaDetalhe({
  vagaId,
  semPerfil,
  onMudou,
}: {
  vagaId: string;
  semPerfil: boolean;
  onMudou: () => void;
}) {
  const { vaga, loading, refetch } = useVaga(vagaId);
  const acoes = useVagaActions();
  const [candidatura, setCandidatura] = useState<GerarCandidaturaResponse | null>(
    null,
  );
  const [curriculo, setCurriculo] = useState<CurriculoVaga | null>(null);
  const [gerarCarta, setGerarCarta] = useState(true);
  const [aviso, setAviso] = useState<string | null>(null);

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
      setAviso('Rascunho gerado. Revise antes de enviar — a ferramenta não envia.');
      onMudou();
    }
  }

  async function handleCurriculo() {
    setAviso(null);
    const r = await acoes.gerarCurriculo(vagaId);
    if (r) {
      setCurriculo(r.curriculo);
      onMudou();
    }
  }

  async function handleStatus(status: VagaStatus) {
    await acoes.atualizar(vagaId, { status });
    refetch();
    onMudou();
  }

  if (loading || !vaga) {
    return <div className="card p-8 h-64 animate-pulse" />;
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Cabeçalho da vaga */}
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
          {typeof vaga.match_score === 'number' && (
            <MatchPill score={vaga.match_score} grande />
          )}
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
        <div className="flex flex-wrap gap-1.5 mt-4">
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
              {acoes.loading ? 'Gerando…' : 'Gerar currículo'}
            </button>
          </div>
        </div>

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
            </div>
          )}
        </div>
      )}

      {/* Currículo ATS gerado */}
      {curriculo && <CurriculoPdf curriculo={curriculo} />}

      {/* Rascunho gerado */}
      {candidatura && <RascunhoCandidatura dados={candidatura} />}
    </div>
  );
}

function RascunhoCandidatura({ dados }: { dados: GerarCandidaturaResponse }) {
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
        <BlocoTexto rotulo="Carta de apresentação" corpo={dados.carta.corpo} />
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

// ── Form de nova vaga ─────────────────────────────────────────────

function NovaVagaForm({
  onSubmit,
  loading,
  erro,
}: {
  onSubmit: (body: VagaCreate) => void;
  loading: boolean;
  erro: string | null;
}) {
  const [f, setF] = useState<VagaCreate>({ titulo: '', descricao: '' });

  function set<K extends keyof VagaCreate>(k: K, v: VagaCreate[K]) {
    setF((prev) => ({ ...prev, [k]: v }));
  }

  return (
    <div className="card p-6 mb-5">
      {erro && (
        <div className="text-[13px] text-brand-ink bg-brand-soft/60 border border-brand/30 rounded p-3 mb-4">
          {erro}
        </div>
      )}
      <div className="grid md:grid-cols-2 gap-4">
        <Campo label="Título da vaga" obrigatorio>
          <input
            className="input"
            value={f.titulo}
            onChange={(e) => set('titulo', e.target.value)}
          />
        </Campo>
        <Campo label="Empresa">
          <input
            className="input"
            value={f.empresa ?? ''}
            onChange={(e) => set('empresa', e.target.value)}
          />
        </Campo>
        <Campo label="Link da vaga">
          <input
            className="input"
            value={f.link ?? ''}
            onChange={(e) => set('link', e.target.value)}
          />
        </Campo>
        <Campo label="E-mail de contato">
          <input
            className="input"
            value={f.contato_email ?? ''}
            onChange={(e) => set('contato_email', e.target.value)}
          />
        </Campo>
        <Campo label="Modelo (remoto/híbrido/presencial)">
          <input
            className="input"
            value={f.modelo ?? ''}
            onChange={(e) => set('modelo', e.target.value)}
          />
        </Campo>
        <Campo label="Senioridade">
          <input
            className="input"
            value={f.senioridade ?? ''}
            onChange={(e) => set('senioridade', e.target.value)}
          />
        </Campo>
      </div>
      <div className="mt-4">
        <Campo label="Descrição da vaga (cole aqui)" obrigatorio>
          <textarea
            className="input resize-y min-h-[140px]"
            value={f.descricao}
            onChange={(e) => set('descricao', e.target.value)}
          />
        </Campo>
      </div>
      <div className="flex justify-end mt-4">
        <button
          type="button"
          className="btn-primary disabled:opacity-40"
          onClick={() => onSubmit(f)}
          disabled={loading}
        >
          {loading ? 'Salvando…' : 'Registrar vaga'}
        </button>
      </div>
    </div>
  );
}

// ── pedaços reutilizáveis ─────────────────────────────────────────

function Campo({
  label,
  obrigatorio,
  children,
}: {
  label: string;
  obrigatorio?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex items-center gap-1 text-xs font-medium text-ink-soft">
        {label}
        {obrigatorio && <span className="text-brand">*</span>}
      </label>
      {children}
    </div>
  );
}

function Tags({
  titulo,
  itens,
  forte,
  ok,
}: {
  titulo: string;
  itens: string[];
  forte?: boolean;
  ok?: boolean;
}) {
  if (!itens || itens.length === 0) return null;
  const cls = ok
    ? 'bg-success-soft text-success-ink'
    : forte
      ? 'bg-brand-soft text-brand-ink'
      : 'bg-bg-alt text-ink-soft';
  return (
    <div className="mb-2.5">
      <div className="text-[11px] font-medium text-ink-mute mb-1">{titulo}</div>
      <div className="flex flex-wrap gap-1.5">
        {itens.map((t, i) => (
          <span
            key={i}
            className={`text-[12px] px-2 py-1 rounded-sm leading-snug ${cls}`}
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

function MatchPill({ score, grande }: { score: number; grande?: boolean }) {
  const cor =
    score >= 70
      ? 'bg-success-soft text-success-ink'
      : score >= 40
        ? 'bg-brand-soft text-brand-ink'
        : 'bg-bg-alt text-ink-mute';
  return (
    <span
      className={[
        'font-mono rounded-sm whitespace-nowrap',
        grande ? 'text-sm px-2.5 py-1' : 'text-[10px] px-1.5 py-0.5',
        cor,
      ].join(' ')}
    >
      {score}%
    </span>
  );
}

function StatusBadge({ status }: { status: VagaStatus }) {
  const cls: Record<VagaStatus, string> = {
    quero_candidatar: 'bg-bg-alt text-ink-soft',
    candidatei: 'bg-brand-soft text-brand-ink',
    respondeu: 'bg-success-soft text-success-ink',
    entrevista: 'bg-success-soft text-success-ink',
    fim: 'bg-bg-alt text-ink-mute',
  };
  return (
    <span
      className={`font-mono text-[10px] uppercase tracking-[0.06em] px-2 py-1 rounded-sm whitespace-nowrap ${cls[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}

function computeStats(items: VagaListItem[]) {
  const c = { quero_candidatar: 0, candidatei: 0, respondeu: 0, entrevista: 0, fim: 0 };
  for (const v of items) c[v.status]++;
  return { ...c, emProcesso: c.respondeu + c.entrevista };
}
