import { useState } from 'react';
import { CopywriterForm } from './CopywriterForm';
import { useCopywriter } from '../hooks/useCopywriter';
import type { EmailGerado } from '../lib/types';

export default function CopywriterScreen() {
  const { gerar, resultado, carregando, erro, limpar } = useCopywriter();

  return (
    <div className="max-w-[1200px] mx-auto">
      <header className="mb-7">
        <div className="eyebrow mb-3">Agente 02 · Copywriting comercial</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Copywriter
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[60ch] leading-relaxed m-0">
          Gera e-mails de prospecção persuasivos e personalizados a partir
          dos dados do lead. Funciona para e-mail e WhatsApp.
        </p>
      </header>

      <div className="mb-6">
        <CopywriterForm onSubmit={gerar} carregando={carregando} />
      </div>

      {erro && (
        <div className="card p-4 mb-4 border-brand/30 bg-brand-soft/40">
          <span className="text-[13px] text-brand-ink">
            <strong>Não deu certo:</strong> {erro}
          </span>
        </div>
      )}

      {carregando && (
        <div className="card p-4 mb-4">
          <span className="text-[13px] text-ink-mute">
            Gerando… isso costuma levar de 10 a 30 segundos.
          </span>
        </div>
      )}

      {resultado && !carregando && (
        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
              Resultado
            </h2>
            <button
              type="button"
              className="btn-ghost"
              onClick={limpar}
            >
              Limpar resultado
            </button>
          </div>

          <EmailCard email={resultado.email} rotulo="Versão principal" />

          {resultado.variantes.length > 0 && (
            <>
              <h3 className="font-display font-semibold text-base text-ink-soft mt-2">
                Variantes para teste A/B
              </h3>
              {resultado.variantes.map((v, i) => (
                <EmailCard
                  key={i}
                  email={v}
                  rotulo={`Variante ${i + 1}`}
                />
              ))}
            </>
          )}
        </section>
      )}
    </div>
  );
}

/* ── Card de um e-mail gerado ──────────────────────────────── */

function EmailCard({
  email,
  rotulo,
}: {
  email: EmailGerado;
  rotulo: string;
}) {
  const [copiado, setCopiado] = useState(false);

  async function copiar() {
    // No WhatsApp o assunto vem vazio — copia só o corpo nesse caso.
    const texto = email.assunto?.trim()
      ? `Assunto: ${email.assunto}\n\n${email.corpo}`
      : email.corpo;
    try {
      await navigator.clipboard.writeText(texto);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      setCopiado(false);
    }
  }

  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-center gap-3 pb-2 border-b border-line">
        <span className="text-sm font-medium text-ink flex-1">{rotulo}</span>
        <span className="font-mono text-[10px] uppercase tracking-[0.08em] bg-brand-soft text-brand-ink px-2 py-0.5 rounded-sm">
          {email.tom}
        </span>
        <button
          type="button"
          className="text-xs font-medium px-3 py-1.5 rounded border border-line text-ink-soft hover:border-brand hover:text-brand transition-colors"
          onClick={copiar}
        >
          {copiado ? '✓ Copiado' : 'Copiar'}
        </button>
      </div>

      {/* Assunto: escondido quando vazio (caso WhatsApp) */}
      {email.assunto?.trim() && (
        <Campo label="Assunto">
          <p className="text-sm text-ink m-0">{email.assunto}</p>
        </Campo>
      )}

      <Campo label="Mensagem">
        {/* whitespace-pre-wrap preserva as quebras de linha da IA */}
        <p className="text-sm text-ink-soft m-0 whitespace-pre-wrap leading-relaxed">
          {email.corpo}
        </p>
      </Campo>

      <Campo label="CTA">
        <p className="text-sm text-brand-ink font-medium m-0">{email.cta}</p>
      </Campo>
    </div>
  );
}

function Campo({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="text-[10.5px] uppercase tracking-[0.1em] font-mono text-ink-mute mb-0.5">
        {label}
      </div>
      {children}
    </div>
  );
}