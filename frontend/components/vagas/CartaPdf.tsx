'use client';

import type { CartaCandidatura, ContatoPessoal } from '@/lib/types';
import { esc, imprimirDocumento, slug, slugNome } from './_pdf';

/**
 * Carta de apresentação como DOCUMENTO pra anexar (a que muitas vagas pedem).
 * PDF gerado via "Imprimir → Salvar como PDF" — mesma mecânica do currículo.
 * Cabeçalho com nome/contato + data + referência da vaga; o corpo é o texto que
 * a IA redigiu (com saudação e assinatura), renderizado em parágrafos.
 */

const linhaContato = (c?: ContatoPessoal | null): string => {
  if (!c) return '';
  return [c.email, c.telefone, c.linkedin, c.github, c.portfolio]
    .filter(Boolean)
    .map((v) => esc(v))
    .join('  ·  ');
};

/** Vira `carta-pabloortiz-{vaga}` (sem `.pdf`; o navegador anexa). */
function nomeArquivoCarta(nome: string, vaga?: string | null): string {
  return ['carta', slugNome(nome), slug(vaga)].filter(Boolean).join('-');
}

function cartaHtml(
  carta: CartaCandidatura,
  nome: string,
  contato?: ContatoPessoal | null,
  empresa?: string | null,
  vagaTitulo?: string | null,
): string {
  const contatoLinha = linhaContato(contato);
  const hoje = new Date().toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
  const paras = String(carta.corpo)
    .trim()
    .split(/\n\s*\n/)
    .filter(Boolean)
    .map((p) => `<p>${esc(p).replace(/\n/g, '<br>')}</p>`)
    .join('');

  return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8" />
<title>${esc(nomeArquivoCarta(nome, vagaTitulo))}</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    font-family: Arial, Helvetica, sans-serif;
    color: #1a1a1a; font-size: 11pt; line-height: 1.5;
    margin: 0; padding: 18mm 20mm;
  }
  h1 { font-size: 20pt; margin: 0 0 2px; font-weight: 700; }
  .contato { font-size: 9.5pt; color: #333; margin: 0; }
  header { border-bottom: 1px solid #999; padding-bottom: 10px; margin-bottom: 22px; }
  .meta { color: #555; font-size: 10pt; margin: 0 0 18px; }
  .meta .dest { color: #1a1a1a; font-weight: 700; margin: 10px 0 0; }
  p { margin: 0 0 11px; text-align: justify; }
  @page { margin: 0; }
</style></head>
<body>
  <header>
    <h1>${esc(nome)}</h1>
    ${contatoLinha ? `<p class="contato">${contatoLinha}</p>` : ''}
  </header>
  <div class="meta">
    <p>${esc(hoje)}</p>
    ${empresa ? `<p class="dest">À ${esc(empresa)}</p>` : ''}
    ${vagaTitulo ? `<p>Ref.: candidatura para ${esc(vagaTitulo)}</p>` : ''}
  </div>
  ${paras}
</body></html>`;
}

export function CartaPdf({
  carta,
  nome,
  contato,
  empresa,
  vagaTitulo,
}: {
  carta: CartaCandidatura;
  nome: string;
  contato?: ContatoPessoal | null;
  empresa?: string | null;
  vagaTitulo?: string | null;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between gap-3 flex-wrap mb-4">
        <h4 className="font-display font-semibold text-sm text-ink m-0">
          Carta de apresentação — sob medida pra esta vaga
        </h4>
        <button
          type="button"
          className="btn-primary"
          onClick={() =>
            imprimirDocumento(
              cartaHtml(carta, nome, contato, empresa, vagaTitulo),
              nomeArquivoCarta(nome, vagaTitulo),
            )
          }
        >
          Baixar PDF (imprimir)
        </button>
      </div>

      {/* Prévia fiel ao PDF */}
      <div className="curriculo-preview border border-line rounded bg-white text-ink p-6 text-[13px] leading-relaxed">
        <div className="font-display font-bold text-xl">{nome}</div>
        {linhaContato(contato) && (
          <div className="text-[12px] text-ink-mute mt-1 border-b border-line pb-3">
            {[
              contato?.email,
              contato?.telefone,
              contato?.linkedin,
              contato?.github,
              contato?.portfolio,
            ]
              .filter(Boolean)
              .join('  ·  ')}
          </div>
        )}
        <div className="text-[12px] text-ink-mute mt-3">
          {new Date().toLocaleDateString('pt-BR', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
          })}
          {empresa ? ` · À ${empresa}` : ''}
          {vagaTitulo ? ` · Ref.: ${vagaTitulo}` : ''}
        </div>
        <div className="mt-4 whitespace-pre-line">{carta.corpo}</div>
      </div>

      <p className="text-[11px] text-ink-mute mt-3">
        Anexe junto com o currículo quando a vaga pedir carta. Revise antes de enviar.
      </p>
    </div>
  );
}
