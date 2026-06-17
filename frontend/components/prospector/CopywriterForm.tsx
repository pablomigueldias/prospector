import { useState } from 'react';
import type { CopywriterRequest } from '@/lib/types';

interface CopywriterFormProps {
  onSubmit: (dados: CopywriterRequest) => void;
  carregando: boolean;
}

const ESTADO_INICIAL: CopywriterRequest = {
  empresa: '',
  segmento: '',
  nome_contato: '',
  cargo: '',
  tipo: 'prospeccao',
  canal: 'email',
  necessidade: '',
  servico: '',
  diferenciais: '',
  contexto_extra: '',
};

const TIPOS = [
  { valor: 'prospeccao', rotulo: 'Prospecção de cliente' },
  { valor: 'parceria', rotulo: 'Parceria comercial' },
  { valor: 'vaga', rotulo: 'Vaga de emprego' },
  { valor: 'freelancer', rotulo: 'Projeto de freelancer' },
];

export function CopywriterForm({ onSubmit, carregando }: CopywriterFormProps) {
  const [dados, setDados] = useState<CopywriterRequest>(ESTADO_INICIAL);
  const [erro, setErro] = useState<string | null>(null);

  function atualizar<K extends keyof CopywriterRequest>(
    campo: K,
    valor: CopywriterRequest[K],
  ) {
    setDados((prev) => ({ ...prev, [campo]: valor }));
    if (erro) setErro(null);
  }

  function handleEnviar() {
    if (!dados.empresa.trim()) {
      setErro('Informe ao menos o nome da empresa alvo.');
      return;
    }
    onSubmit(dados);
  }

  function handleLimpar() {
    setDados(ESTADO_INICIAL);
    setErro(null);
  }

  return (
    <section className="card p-7">
      <FormSectionHeader
        title="Dados para o e-mail"
        help="Só a empresa é obrigatória. Quanto mais campos, melhor a personalização."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4 mb-6">
        <Field label="Empresa alvo" required>
          <input
            type="text"
            className="input"
            value={dados.empresa}
            onChange={(e) => atualizar('empresa', e.target.value)}
            placeholder="Ex: Clínica Vida Saudável"
            disabled={carregando}
          />
        </Field>

        <Field label="Segmento / Nicho">
          <input
            type="text"
            className="input"
            value={dados.segmento ?? ''}
            onChange={(e) => atualizar('segmento', e.target.value)}
            placeholder="Ex: Saúde, Varejo, Educação"
            disabled={carregando}
          />
        </Field>

        <Field label="Nome do contato">
          <input
            type="text"
            className="input"
            value={dados.nome_contato ?? ''}
            onChange={(e) => atualizar('nome_contato', e.target.value)}
            placeholder="Ex: Maria Souza"
            disabled={carregando}
          />
        </Field>

        <Field label="Cargo">
          <input
            type="text"
            className="input"
            value={dados.cargo ?? ''}
            onChange={(e) => atualizar('cargo', e.target.value)}
            placeholder="Ex: Diretora de Operações"
            disabled={carregando}
          />
        </Field>

        <Field label="Tipo de abordagem">
          <select
            className="input"
            value={dados.tipo}
            onChange={(e) => atualizar('tipo', e.target.value)}
            disabled={carregando}
          >
            {TIPOS.map((t) => (
              <option key={t.valor} value={t.valor}>
                {t.rotulo}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Canal">
          <select
            className="input"
            value={dados.canal ?? 'email'}
            onChange={(e) => atualizar('canal', e.target.value)}
            disabled={carregando}
          >
            <option value="email">E-mail</option>
            <option value="whatsapp">WhatsApp</option>
          </select>
        </Field>
      </div>

      <Divider />

      <FormSectionHeader
        title="Contexto da oferta (opcional)"
        help="Detalhes que ajudam a IA a escrever algo específico, não genérico."
      />

      <div className="grid grid-cols-1 gap-y-4 mb-6">
        <Field label="Necessidade identificada">
          <input
            type="text"
            className="input"
            value={dados.necessidade ?? ''}
            onChange={(e) => atualizar('necessidade', e.target.value)}
            placeholder="Ex: site lento e sem agendamento online"
            disabled={carregando}
          />
        </Field>

        <Field label="Serviço oferecido">
          <input
            type="text"
            className="input"
            value={dados.servico ?? ''}
            onChange={(e) => atualizar('servico', e.target.value)}
            placeholder="Ex: novo site com sistema de agendamento integrado"
            disabled={carregando}
          />
        </Field>

        <Field label="Diferenciais da Reative Systems">
          <input
            type="text"
            className="input"
            value={dados.diferenciais ?? ''}
            onChange={(e) => atualizar('diferenciais', e.target.value)}
            placeholder="Ex: entrega em 3 semanas, suporte contínuo"
            disabled={carregando}
          />
        </Field>

        <Field
          label="Contexto adicional"
          help="Cole aqui a descrição da vaga/projeto, se houver."
        >
          <textarea
            className="input resize-y min-h-[88px]"
            rows={4}
            value={dados.contexto_extra ?? ''}
            onChange={(e) => atualizar('contexto_extra', e.target.value)}
            placeholder="Texto livre — ex: descrição copiada de uma plataforma de freelancer."
            disabled={carregando}
          />
        </Field>
      </div>

      {erro && (
        <div className="text-[13px] text-brand-ink bg-brand-soft/60 border border-brand/30 rounded p-3 mb-4">
          {erro}
        </div>
      )}

      <div className="flex items-center justify-end gap-3">
        <button
          type="button"
          className="btn-ghost disabled:opacity-40 disabled:cursor-not-allowed"
          onClick={handleLimpar}
          disabled={carregando}
        >
          Limpar
        </button>
        <button
          type="button"
          className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
          onClick={handleEnviar}
          disabled={carregando}
        >
          {carregando ? 'Gerando…' : 'Gerar e-mail'}
        </button>
      </div>
    </section>
  );
}

/* ── Auxiliares de layout ──────────────────────────────────── */

function FormSectionHeader({ title, help }: { title: string; help: string }) {
  return (
    <div className="mb-4">
      <h3 className="font-display font-semibold text-sm tracking-tight text-ink mb-1">
        {title}
      </h3>
      <p className="text-xs text-ink-mute">{help}</p>
    </div>
  );
}

function Field({
  label,
  required,
  help,
  children,
}: {
  label: string;
  required?: boolean;
  help?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex items-center gap-1 text-xs font-medium text-ink-soft">
        {label}
        {required && <span className="text-brand">*</span>}
      </label>
      {children}
      {help && <span className="text-[11px] text-ink-faint">{help}</span>}
    </div>
  );
}

function Divider() {
  return <div className="h-px bg-line mt-2 mb-5" />;
}