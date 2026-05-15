import { FormEvent, useState } from 'react';

import {
  IconAlertCircle,
  IconArrowRight,
  IconBolt,
  IconCheck,
  IconEye,
  IconFacebook,
  IconId,
  IconInstagram,
  IconLinkedin,
  IconLoader,
  IconMail,
  IconPhone,
  IconWhatsApp,
  IconWorld,
  IconX,
} from './Icon';
import {
  useProspectorPreview,
  useProspectorRun,
} from '@/hooks/useProspector';
import { formatCnpj } from '@/lib/format';
import type { ProspectorManualRequest } from '@/lib/types';

interface ProspectorFormProps {
  onLeadCreated?: () => void;
}

export function ProspectorForm({ onLeadCreated }: ProspectorFormProps) {
  const [form, setForm] = useState({
    cnpj: '',
    site: '',
    instagram: '',
    facebook: '',
    linkedin: '',
    email: '',
    telefone: '',
    whatsapp: '',
  });

  const preview = useProspectorPreview();
  const run = useProspectorRun();

  function setField<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function buildRequest(): ProspectorManualRequest | null {
    if (!form.cnpj) return null;
    return {
      cnpj: form.cnpj,
      site: form.site || null,
      instagram: form.instagram || null,
      facebook: form.facebook || null,
      linkedin: form.linkedin || null,
      email: form.email || null,
      telefone: form.telefone || null,
      whatsapp: form.whatsapp || null,
    };
  }

  async function handlePreview(e: FormEvent) {
    e.preventDefault();
    const body = buildRequest();
    if (!body) return;
    await preview.execute(body);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const body = buildRequest();
    if (!body) return;
    const result = await run.execute(body);
    if (result?.success) {
      setForm({
        cnpj: '',
        site: '',
        instagram: '',
        facebook: '',
        linkedin: '',
        email: '',
        telefone: '',
        whatsapp: '',
      });
      preview.reset();
      onLeadCreated?.();
    }
  }

  const isBusy = preview.loading || run.loading;
  const errorMessage = run.error?.message ?? preview.error?.message ?? null;
  const previewLead = preview.data?.lead ?? null;
  const runResult = run.data ?? null;

  return (
    <section className="card p-7">
      <form onSubmit={handleSubmit} noValidate>
        <FormSectionHeader
          title="Dados da empresa"
          help="CNPJ é obrigatório. Site é opcional, mas melhora muito a análise da IA."
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4 mb-6">
          <Field icon={<IconId />} label="CNPJ" required>
            <input
              type="text"
              className="input"
              value={form.cnpj}
              onChange={(e) => setField('cnpj', formatCnpj(e.target.value))}
              placeholder="00.000.000/0000-00"
              disabled={isBusy}
              maxLength={18}
              autoComplete="off"
              inputMode="numeric"
            />
            <FieldHelp>Valida o dígito antes de consultar</FieldHelp>
          </Field>

          <Field icon={<IconWorld />} label="Site">
            <input
              type="url"
              className="input"
              value={form.site}
              onChange={(e) => setField('site', e.target.value)}
              placeholder="https://empresa.com.br"
              disabled={isBusy}
              autoComplete="url"
            />
            <FieldHelp>Será scrapeado pra extrair contatos</FieldHelp>
          </Field>
        </div>

        <Divider />

        <FormSectionHeader
          title="Redes sociais (opcional)"
          help="Sobrescrevem o que o scraping encontrar. Aceita @handle, slug ou URL completa."
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-5 gap-y-4 mb-6">
          <Field icon={<IconInstagram />} label="Instagram da empresa">
            <input
              type="text"
              className="input"
              value={form.instagram}
              onChange={(e) => setField('instagram', e.target.value)}
              placeholder="@empresa"
              disabled={isBusy}
            />
          </Field>
          <Field icon={<IconFacebook />} label="Facebook da empresa">
            <input
              type="text"
              className="input"
              value={form.facebook}
              onChange={(e) => setField('facebook', e.target.value)}
              placeholder="empresa"
              disabled={isBusy}
            />
          </Field>
          <Field icon={<IconLinkedin />} label="LinkedIn do decisor">
            <input
              type="text"
              className="input"
              value={form.linkedin}
              onChange={(e) => setField('linkedin', e.target.value)}
              placeholder="joao-silva"
              disabled={isBusy}
            />
          </Field>
        </div>

        <Divider />

        <FormSectionHeader
          title="Contato direto (opcional)"
          help="Se você já tem o contato comercial em mãos, agiliza pular o scraping."
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-5 gap-y-4 mb-6">
          <Field icon={<IconMail />} label="Email">
            <input
              type="email"
              className="input"
              value={form.email}
              onChange={(e) => setField('email', e.target.value)}
              placeholder="contato@empresa.com.br"
              disabled={isBusy}
              autoComplete="email"
            />
          </Field>
          <Field icon={<IconPhone />} label="Telefone">
            <input
              type="tel"
              className="input"
              value={form.telefone}
              onChange={(e) => setField('telefone', e.target.value)}
              placeholder="(11) 3234-5678"
              disabled={isBusy}
              autoComplete="tel"
            />
          </Field>
          <Field icon={<IconWhatsApp />} label="WhatsApp">
            <input
              type="tel"
              className="input"
              value={form.whatsapp}
              onChange={(e) => setField('whatsapp', e.target.value)}
              placeholder="(11) 99208-0886"
              disabled={isBusy}
            />
          </Field>
        </div>

        <PipelineStatus busy={isBusy} stage={runStage(preview, run)} />

        {errorMessage && !isBusy && (
          <div className="flex items-start gap-2.5 mb-4 p-3 rounded bg-brand-soft/60 border border-brand/30">
            <IconAlertCircle className="text-base text-brand mt-0.5 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-medium text-brand-ink">
                Não foi possível concluir
              </div>
              <div className="text-[12.5px] text-brand-ink/80 mt-0.5">
                {errorMessage}
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                preview.reset();
                run.reset();
              }}
              className="text-brand-ink/60 hover:text-brand-ink"
              aria-label="Dispensar erro"
            >
              <IconX className="text-base" />
            </button>
          </div>
        )}

        {runResult?.success && !isBusy && (
          <div className="flex items-start gap-2.5 mb-4 p-3 rounded bg-success-soft/60 border border-success/30">
            <IconCheck className="text-base text-success mt-0.5 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-medium text-success-ink">
                Lead criado no Notion!
              </div>
              <div className="text-[12.5px] text-success-ink/80 mt-0.5">
                {runResult.lead.empresa.nome ?? 'Empresa'} ·{' '}
                {runResult.notion_contatos_ids.length} contato(s) ·{' '}
                fonte: {runResult.fonte_cnpj?.toUpperCase() ?? '?'}
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={handlePreview}
            className="btn-ghost disabled:opacity-40 disabled:cursor-not-allowed"
            disabled={!form.cnpj || isBusy}
          >
            {preview.loading ? (
              <>
                <IconLoader className="text-base" /> Pré-visualizando…
              </>
            ) : (
              <>
                <IconEye className="text-base" /> Pré-visualizar lead
              </>
            )}
          </button>
          <button
            type="submit"
            className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
            disabled={!form.cnpj || isBusy}
          >
            {run.loading ? (
              <>
                <IconLoader className="text-base" /> Processando pipeline…
              </>
            ) : (
              <>
                Prospectar e enviar pro Notion
                <IconArrowRight className="text-base" />
              </>
            )}
          </button>
        </div>
      </form>

      {previewLead && !run.data && !preview.loading && (
        <PreviewPanel
          lead={previewLead}
          fonte={preview.data?.fonte_cnpj ?? null}
          onDismiss={() => preview.reset()}
        />
      )}
    </section>
  );
}

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
  icon,
  label,
  required,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex items-center gap-1.5 text-xs font-medium text-ink-soft">
        <span className="text-sm text-ink-mute">{icon}</span>
        {label}
        {required && <span className="text-brand">*</span>}
      </label>
      {children}
    </div>
  );
}

function FieldHelp({ children }: { children: React.ReactNode }) {
  return <span className="text-[11px] text-ink-faint">{children}</span>;
}

function Divider() {
  return <div className="h-px bg-line mt-2 mb-5" />;
}

function PipelineStatus({
  busy,
  stage,
}: {
  busy: boolean;
  stage: string;
}) {
  return (
    <div className="flex items-center gap-2.5 px-4 py-3 bg-brand-soft rounded mb-5">
      <span className="text-brand text-lg shrink-0">
        {busy ? <IconLoader /> : <IconBolt />}
      </span>
      <div className="flex-1 min-w-0">
        <div className="text-[12.5px] font-medium text-brand-ink">{stage}</div>
        <div className="font-mono text-[11px] text-brand-ink/70 mt-0.5 truncate">
          BrasilAPI → fallback OpenCNPJ → scraping → análise IA → Notion
        </div>
      </div>
    </div>
  );
}

function PreviewPanel({
  lead,
  fonte,
  onDismiss,
}: {
  lead: import('@/lib/types').Lead;
  fonte: string | null;
  onDismiss: () => void;
}) {
  const emp = lead.empresa;
  return (
    <div className="mt-6 border border-line rounded bg-bg-alt/50">
      <div className="flex items-center justify-between px-4 py-3 border-b border-line">
        <div className="flex items-center gap-2">
          <IconEye className="text-base text-ink-mute" />
          <span className="text-sm font-medium text-ink">
            Pré-visualização
          </span>
          {fonte && (
            <span className="font-mono text-[9.5px] uppercase tracking-[0.08em] bg-brand-soft text-brand-ink px-1.5 py-0.5 rounded-sm">
              via {fonte}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="text-ink-mute hover:text-ink"
          aria-label="Fechar pré-visualização"
        >
          <IconX className="text-base" />
        </button>
      </div>

      <div className="p-4 grid grid-cols-2 gap-x-6 gap-y-2 text-[13px]">
        <PreviewField label="Nome" value={emp.nome} />
        <PreviewField label="Razão social" value={emp.razao_social} />
        <PreviewField label="CNPJ" value={emp.cnpj} mono />
        <PreviewField label="Cidade/UF" value={[emp.cidade, emp.estado].filter(Boolean).join('/')} />
        <PreviewField label="Setor" value={emp.setor} highlight />
        <PreviewField label="Tamanho" value={emp.tamanho} highlight />
        <PreviewField
          label="Capital social"
          value={
            emp.capital_social != null
              ? `R$ ${emp.capital_social.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
              : null
          }
          mono
        />
        <PreviewField label="Contatos" value={`${lead.contatos.length}`} />
      </div>

      {emp.notas && (
        <div className="px-4 pb-4">
          <div className="text-[11px] uppercase tracking-[0.1em] font-mono text-ink-mute mb-1.5">
            Notas
          </div>
          <pre className="font-mono text-[11.5px] text-ink-soft bg-surface p-3 rounded border border-line whitespace-pre-wrap max-h-40 overflow-y-auto">
            {emp.notas}
          </pre>
        </div>
      )}
    </div>
  );
}

function PreviewField({
  label,
  value,
  mono,
  highlight,
}: {
  label: string;
  value: string | null | undefined;
  mono?: boolean;
  highlight?: boolean;
}) {
  return (
    <div>
      <div className="text-[10.5px] uppercase tracking-[0.1em] font-mono text-ink-mute">
        {label}
      </div>
      <div
        className={[
          'mt-0.5',
          mono && 'font-mono',
          highlight && 'text-brand-ink font-medium',
          !highlight && 'text-ink',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {value || <span className="text-ink-faint">—</span>}
      </div>
    </div>
  );
}

function runStage(
  preview: { loading: boolean },
  run: { loading: boolean },
): string {
  if (run.loading)
    return 'Executando pipeline completo (CNPJ → site → IA → Notion)…';
  if (preview.loading) return 'Buscando dados do CNPJ…';
  return 'Pipeline configurado';
}
