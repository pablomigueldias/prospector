import { useEffect, useState } from 'react';

import { usePerfil, useSalvarPerfil } from '@/hooks/usePerfil';
import { api } from '@/lib/api';
import type {
  BlocoCurriculo,
  Certificacao as CertificacaoT,
  ExperienciaPerfil as ExperienciaT,
  FormacaoPerfil as FormacaoT,
  Habilidade,
  PerfilMestre,
  ProjetoPerfil,
} from '@/lib/types';

const PERFIL_VAZIO: PerfilMestre = {
  nome: '',
  titulo: '',
  resumo: '',
  tom_escrita: '',
  habilidades: [],
  projetos: [],
  experiencias: [],
  formacao: [],
  certificacoes: [],
  o_que_procuro: { stack: [], modelo: '', tipo_empresa: '', observacoes: '' },
  blocos_curriculo: [],
  contato: { email: '', linkedin: '', github: '', portfolio: '' },
};

export default function PerfilMestreScreen() {
  const { perfil, loading, refetch } = usePerfil();
  const { salvar, loading: salvando, error } = useSalvarPerfil();

  const [form, setForm] = useState<PerfilMestre>(PERFIL_VAZIO);
  const [aviso, setAviso] = useState<string | null>(null);
  const [sincronizando, setSincronizando] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  useEffect(() => {
    if (perfil) {
      setForm({ ...PERFIL_VAZIO, ...perfil });
    }
  }, [perfil]);

  function set<K extends keyof PerfilMestre>(key: K, value: PerfilMestre[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSalvar() {
    setAviso(null);
    if (!form.nome.trim()) {
      setAviso('O perfil precisa de um nome.');
      return;
    }
    const r = await salvar(form);
    if (r) {
      setAviso('Perfil salvo. Agora os agentes pessoais sabem quem você é.');
      refetch();
    }
  }

  async function handleSincronizarCerts() {
    setSyncMsg(null);
    setSincronizando(true);
    try {
      const r = await api.perfilSincronizarCertificados();
      setSyncMsg(
        `Sincronizado: ${r.novos} novo(s), ${r.ja_existiam} já existia(m)` +
          (r.falhas ? `, ${r.falhas} falha(s) — rode de novo` : '') +
          `. Total: ${r.total_no_perfil}` +
          (r.arquivados ? `. ${r.arquivados} PDF(s) guardado(s) no servidor` : '') +
          ` (${r.total_arquivados} arquivado(s)).`,
      );
      refetch();
    } catch (err) {
      setSyncMsg(
        err instanceof Error ? `Falha: ${err.message}` : 'Falha ao sincronizar.',
      );
    } finally {
      setSincronizando(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-[900px] mx-auto">
        <div className="card p-8 animate-pulse h-40" />
      </div>
    );
  }

  return (
    <div className="max-w-[900px] mx-auto pb-16">
      <header className="mb-7">
        <div className="eyebrow mb-3">Pessoal · Perfil Mestre</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Perfil Mestre
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[60ch] leading-relaxed m-0">
          Quem VOCÊ é. É a referência que a IA usa pra medir match com vagas e
          escrever candidatura no seu tom. Preencha com a verdade — a ferramenta
          reorganiza o que está aqui, nunca inventa.
        </p>
      </header>

      {/* Identidade */}
      <Secao titulo="Identidade">
        <div className="grid md:grid-cols-2 gap-4">
          <Campo label="Nome" obrigatorio>
            <input
              className="input"
              value={form.nome}
              onChange={(e) => set('nome', e.target.value)}
            />
          </Campo>
          <Campo label="Título (ex: Dev Full-Stack)">
            <input
              className="input"
              value={form.titulo ?? ''}
              onChange={(e) => set('titulo', e.target.value)}
            />
          </Campo>
        </div>
        <Campo label="Resumo / bio curta">
          <textarea
            className="input resize-y min-h-[72px]"
            value={form.resumo ?? ''}
            onChange={(e) => set('resumo', e.target.value)}
          />
        </Campo>
        <Campo
          label="Tom de escrita"
          ajuda="Exemplos de como VOCÊ escreve, pra carta não soar como IA genérica."
        >
          <textarea
            className="input resize-y min-h-[88px]"
            value={form.tom_escrita ?? ''}
            onChange={(e) => set('tom_escrita', e.target.value)}
          />
        </Campo>
      </Secao>

      {/* Contato */}
      <Secao titulo="Contato">
        <div className="grid md:grid-cols-2 gap-4">
          <Campo label="E-mail">
            <input
              className="input"
              value={form.contato?.email ?? ''}
              onChange={(e) =>
                set('contato', { ...form.contato, email: e.target.value })
              }
            />
          </Campo>
          <Campo label="LinkedIn">
            <input
              className="input"
              value={form.contato?.linkedin ?? ''}
              onChange={(e) =>
                set('contato', { ...form.contato, linkedin: e.target.value })
              }
            />
          </Campo>
          <Campo label="GitHub">
            <input
              className="input"
              value={form.contato?.github ?? ''}
              onChange={(e) =>
                set('contato', { ...form.contato, github: e.target.value })
              }
            />
          </Campo>
          <Campo label="Portfólio">
            <input
              className="input"
              value={form.contato?.portfolio ?? ''}
              onChange={(e) =>
                set('contato', { ...form.contato, portfolio: e.target.value })
              }
            />
          </Campo>
        </div>
      </Secao>

      {/* O que procuro */}
      <Secao titulo="O que procuro">
        <Campo label="Stack desejada (separe por vírgula)">
          <input
            className="input"
            value={(form.o_que_procuro?.stack ?? []).join(', ')}
            onChange={(e) =>
              set('o_que_procuro', {
                ...form.o_que_procuro,
                stack: splitCSV(e.target.value),
              })
            }
          />
        </Campo>
        <div className="grid md:grid-cols-2 gap-4">
          <Campo label="Modelo (remoto/híbrido/presencial)">
            <input
              className="input"
              value={form.o_que_procuro?.modelo ?? ''}
              onChange={(e) =>
                set('o_que_procuro', {
                  ...form.o_que_procuro,
                  stack: form.o_que_procuro?.stack ?? [],
                  modelo: e.target.value,
                })
              }
            />
          </Campo>
          <Campo label="Tipo de empresa">
            <input
              className="input"
              value={form.o_que_procuro?.tipo_empresa ?? ''}
              onChange={(e) =>
                set('o_que_procuro', {
                  ...form.o_que_procuro,
                  stack: form.o_que_procuro?.stack ?? [],
                  tipo_empresa: e.target.value,
                })
              }
            />
          </Campo>
        </div>
      </Secao>

      {/* Habilidades */}
      <ListaSecao<Habilidade>
        titulo="Habilidades técnicas"
        itens={form.habilidades}
        onChange={(v) => set('habilidades', v)}
        vazio={{ nome: '', nivel: '', onde_usou: '' }}
        rotuloAdd="Adicionar habilidade"
        render={(item, upd) => (
          <div className="grid md:grid-cols-3 gap-3">
            <input
              className="input"
              placeholder="Habilidade (ex: React)"
              value={item.nome}
              onChange={(e) => upd({ ...item, nome: e.target.value })}
            />
            <input
              className="input"
              placeholder="Nível (ex: avançado)"
              value={item.nivel ?? ''}
              onChange={(e) => upd({ ...item, nivel: e.target.value })}
            />
            <input
              className="input"
              placeholder="Onde usou"
              value={item.onde_usou ?? ''}
              onChange={(e) => upd({ ...item, onde_usou: e.target.value })}
            />
          </div>
        )}
      />

      {/* Projetos */}
      <ListaSecao<ProjetoPerfil>
        titulo="Projetos"
        itens={form.projetos}
        onChange={(v) => set('projetos', v)}
        vazio={{ nome: '', descricao: '', prova: '', stack: [], link: '' }}
        rotuloAdd="Adicionar projeto"
        render={(item, upd) => (
          <div className="flex flex-col gap-3">
            <div className="grid md:grid-cols-2 gap-3">
              <input
                className="input"
                placeholder="Nome do projeto"
                value={item.nome}
                onChange={(e) => upd({ ...item, nome: e.target.value })}
              />
              <input
                className="input"
                placeholder="Link"
                value={item.link ?? ''}
                onChange={(e) => upd({ ...item, link: e.target.value })}
              />
            </div>
            <input
              className="input"
              placeholder="O que este projeto PROVA"
              value={item.prova ?? ''}
              onChange={(e) => upd({ ...item, prova: e.target.value })}
            />
            <input
              className="input"
              placeholder="Stack (separe por vírgula)"
              value={item.stack.join(', ')}
              onChange={(e) => upd({ ...item, stack: splitCSV(e.target.value) })}
            />
            <textarea
              className="input resize-y min-h-[60px]"
              placeholder="Descrição"
              value={item.descricao ?? ''}
              onChange={(e) => upd({ ...item, descricao: e.target.value })}
            />
          </div>
        )}
      />

      {/* Experiência */}
      <ListaSecao<ExperienciaT>
        titulo="Experiência"
        itens={form.experiencias}
        onChange={(v) => set('experiencias', v)}
        vazio={{ empresa: '', cargo: '', periodo: '', descricao: '' }}
        rotuloAdd="Adicionar experiência"
        render={(item, upd) => (
          <div className="flex flex-col gap-3">
            <div className="grid md:grid-cols-3 gap-3">
              <input
                className="input"
                placeholder="Cargo"
                value={item.cargo ?? ''}
                onChange={(e) => upd({ ...item, cargo: e.target.value })}
              />
              <input
                className="input"
                placeholder="Empresa"
                value={item.empresa ?? ''}
                onChange={(e) => upd({ ...item, empresa: e.target.value })}
              />
              <input
                className="input"
                placeholder="Período (ex: 2022–2024)"
                value={item.periodo ?? ''}
                onChange={(e) => upd({ ...item, periodo: e.target.value })}
              />
            </div>
            <textarea
              className="input resize-y min-h-[60px]"
              placeholder="O que fez / resultados"
              value={item.descricao ?? ''}
              onChange={(e) => upd({ ...item, descricao: e.target.value })}
            />
          </div>
        )}
      />

      {/* Formação */}
      <ListaSecao<FormacaoT>
        titulo="Formação"
        itens={form.formacao}
        onChange={(v) => set('formacao', v)}
        vazio={{ instituicao: '', curso: '', periodo: '' }}
        rotuloAdd="Adicionar formação"
        render={(item, upd) => (
          <div className="grid md:grid-cols-3 gap-3">
            <input
              className="input"
              placeholder="Curso"
              value={item.curso ?? ''}
              onChange={(e) => upd({ ...item, curso: e.target.value })}
            />
            <input
              className="input"
              placeholder="Instituição"
              value={item.instituicao ?? ''}
              onChange={(e) => upd({ ...item, instituicao: e.target.value })}
            />
            <input
              className="input"
              placeholder="Período"
              value={item.periodo ?? ''}
              onChange={(e) => upd({ ...item, periodo: e.target.value })}
            />
          </div>
        )}
      />

      {/* Certificações — sync autônomo do Drive */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <p className="text-[13px] text-ink-soft m-0">
          Jogue os PDFs na pasta do Drive e clique pra puxar — o sistema baixa,
          lê cada certificado e preenche os campos sozinho.
        </p>
        <div className="flex items-center gap-3">
          {syncMsg && <span className="text-[13px] text-ink-soft">{syncMsg}</span>}
          <button
            type="button"
            className="btn-ghost disabled:opacity-40 disabled:cursor-not-allowed"
            onClick={handleSincronizarCerts}
            disabled={sincronizando}
          >
            {sincronizando ? 'Sincronizando…' : 'Sincronizar do Drive'}
          </button>
        </div>
      </div>
      <ListaSecao<CertificacaoT>
        titulo="Certificações"
        itens={form.certificacoes}
        onChange={(v) => set('certificacoes', v)}
        vazio={{ nome: '', tema: '', instituicao: '', ano: '', carga_horaria: '', prova: '' }}
        rotuloAdd="Adicionar certificação"
        render={(item, upd) => (
          <div className="flex flex-col gap-3">
            <div className="grid md:grid-cols-4 gap-3">
              <input
                className="input md:col-span-2"
                placeholder="Nome do certificado"
                value={item.nome}
                onChange={(e) => upd({ ...item, nome: e.target.value })}
              />
              <input
                className="input"
                placeholder="Tema (ex: IA/ML)"
                value={item.tema ?? ''}
                onChange={(e) => upd({ ...item, tema: e.target.value })}
              />
              <input
                className="input"
                placeholder="Carga horária"
                value={item.carga_horaria ?? ''}
                onChange={(e) => upd({ ...item, carga_horaria: e.target.value })}
              />
            </div>
            <div className="grid md:grid-cols-3 gap-3">
              <input
                className="input"
                placeholder="Instituição / emissor"
                value={item.instituicao ?? ''}
                onChange={(e) => upd({ ...item, instituicao: e.target.value })}
              />
              <input
                className="input"
                placeholder="Data / ano"
                value={item.ano ?? ''}
                onChange={(e) => upd({ ...item, ano: e.target.value })}
              />
              <input
                className="input"
                placeholder="O que comprova"
                value={item.prova ?? ''}
                onChange={(e) => upd({ ...item, prova: e.target.value })}
              />
            </div>
          </div>
        )}
      />

      {/* Blocos de currículo */}
      <ListaSecao<BlocoCurriculo>
        titulo="Blocos de currículo reutilizáveis"
        itens={form.blocos_curriculo}
        onChange={(v) => set('blocos_curriculo', v)}
        vazio={{ titulo: '', conteudo: '', tags: [] }}
        rotuloAdd="Adicionar bloco"
        render={(item, upd) => (
          <div className="flex flex-col gap-3">
            <div className="grid md:grid-cols-2 gap-3">
              <input
                className="input"
                placeholder="Título do bloco"
                value={item.titulo}
                onChange={(e) => upd({ ...item, titulo: e.target.value })}
              />
              <input
                className="input"
                placeholder="Tags (separe por vírgula)"
                value={item.tags.join(', ')}
                onChange={(e) => upd({ ...item, tags: splitCSV(e.target.value) })}
              />
            </div>
            <textarea
              className="input resize-y min-h-[60px]"
              placeholder="Conteúdo (parágrafo/bullets prontos)"
              value={item.conteudo}
              onChange={(e) => upd({ ...item, conteudo: e.target.value })}
            />
          </div>
        )}
      />

      {/* Barra de ação fixa */}
      <div className="sticky bottom-0 mt-8 bg-surface/90 backdrop-blur border-t border-line py-4 flex items-center justify-between gap-4">
        <div className="text-[13px] min-h-[20px]">
          {aviso && <span className="text-ink-soft">{aviso}</span>}
          {error && <span className="text-brand-ink">{error.message}</span>}
        </div>
        <button
          type="button"
          className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
          onClick={handleSalvar}
          disabled={salvando}
        >
          {salvando ? 'Salvando…' : 'Salvar perfil'}
        </button>
      </div>
    </div>
  );
}

// ── helpers ───────────────────────────────────────────────────────

function splitCSV(v: string): string[] {
  return v
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

function Secao({
  titulo,
  children,
}: {
  titulo: string;
  children: React.ReactNode;
}) {
  return (
    <section className="card p-6 mb-5">
      <h2 className="font-display font-semibold text-base tracking-tight text-ink mb-4">
        {titulo}
      </h2>
      <div className="flex flex-col gap-4">{children}</div>
    </section>
  );
}

function Campo({
  label,
  obrigatorio,
  ajuda,
  children,
}: {
  label: string;
  obrigatorio?: boolean;
  ajuda?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex items-center gap-1 text-xs font-medium text-ink-soft">
        {label}
        {obrigatorio && <span className="text-brand">*</span>}
      </label>
      {children}
      {ajuda && <span className="text-[11px] text-ink-faint">{ajuda}</span>}
    </div>
  );
}

function ListaSecao<T>({
  titulo,
  itens,
  onChange,
  vazio,
  rotuloAdd,
  render,
}: {
  titulo: string;
  itens: T[];
  onChange: (itens: T[]) => void;
  vazio: T;
  rotuloAdd: string;
  render: (item: T, upd: (novo: T) => void) => React.ReactNode;
}) {
  function atualizar(idx: number, novo: T) {
    onChange(itens.map((it, i) => (i === idx ? novo : it)));
  }
  function remover(idx: number) {
    onChange(itens.filter((_, i) => i !== idx));
  }
  return (
    <section className="card p-6 mb-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-base tracking-tight text-ink m-0">
          {titulo}
        </h2>
        <button
          type="button"
          className="btn-ghost text-[13px]"
          onClick={() => onChange([...itens, { ...vazio }])}
        >
          + {rotuloAdd}
        </button>
      </div>

      {itens.length === 0 && (
        <p className="text-[13px] text-ink-mute">Nada por aqui ainda.</p>
      )}

      <div className="flex flex-col gap-4">
        {itens.map((item, idx) => (
          <div
            key={idx}
            className="relative border border-line rounded-lg p-4 pt-4"
          >
            <button
              type="button"
              className="absolute -top-2.5 -right-2.5 w-6 h-6 rounded-full bg-bg-alt border border-line text-ink-mute hover:text-brand hover:border-brand text-sm leading-none"
              onClick={() => remover(idx)}
              aria-label="Remover"
            >
              ×
            </button>
            {render(item, (novo) => atualizar(idx, novo))}
          </div>
        ))}
      </div>
    </section>
  );
}
