'use client';

import type { CurriculoVaga } from '@/lib/types';

/**
 * Currículo ATS-friendly: coluna única, fonte web-safe, títulos de seção
 * padrão e texto selecionável (PDF gerado via "Imprimir → Salvar como PDF",
 * sem dependência extra). Layout fiel ao modelo aprovado.
 *
 * ATS = Applicant Tracking System. O que faz o currículo escalar no ranking:
 * 1) parsing limpo (sem tabela/coluna/ícone) e 2) palavras-chave EXATAS da vaga
 * — essas vêm do texto que a IA gera espelhando a descrição.
 */

const esc = (s?: string | null): string =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

/** Vira "Pablo Dias" → "pablo-dias" (sem acento, minúsculo, hífen). */
const slug = (s?: string | null): string =>
  String(s ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60);

/**
 * Nome do candidato pro arquivo: só primeiro + último nome, colados sem
 * separador ("Pablo Miguel Dias Ortiz" → "pabloortiz").
 */
const slugNome = (s?: string | null): string => {
  const partes = String(s ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]+/g, ' ')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!partes.length) return '';
  const nome = partes.length === 1 ? partes : [partes[0], partes[partes.length - 1]];
  return nome.join('').slice(0, 40);
};

/**
 * Nome do arquivo que o navegador sugere no "Salvar como PDF" — ele usa o
 * <title> do documento. Vira `curriculo-pabloortiz-{vaga}` (sem `.pdf`; o
 * navegador anexa a extensão).
 */
function nomeArquivoPdf(nome: string, vaga?: string | null): string {
  return ['curriculo', slugNome(nome), slug(vaga)].filter(Boolean).join('-');
}

const linhaContato = (c: CurriculoVaga['contato']): string => {
  if (!c) return '';
  const partes = [c.email, c.telefone, c.linkedin, c.github, c.portfolio]
    .filter(Boolean)
    .map((v) => esc(v));
  return partes.join('  ·  ');
};

/** Monta o documento HTML completo do currículo (isolado do CSS do app).
 *  `vagaTitulo` entra só no <title> → nome sugerido do PDF. */
export function curriculoHtml(c: CurriculoVaga, vagaTitulo?: string | null): string {
  const competencias = c.competencias
    .filter((g) => g.itens.length)
    .map(
      (g) =>
        `<p class="comp"><span class="comp-cat">${esc(
          g.categoria,
        )}</span><span class="comp-itens">${g.itens
          .map(esc)
          .join('  ·  ')}</span></p>`,
    )
    .join('');

  const experiencias = c.experiencias
    .map((e) => {
      const head = [esc(e.cargo), esc(e.empresa)].filter(Boolean).join(' · ');
      const bullets = e.bullets
        .filter(Boolean)
        .map((b) => `<li>${esc(b)}</li>`)
        .join('');
      return `<div class="item">
        <div class="item-head"><span class="item-titulo">${head}</span>${
          e.periodo ? `<span class="item-per">${esc(e.periodo)}</span>` : ''
        }</div>
        ${bullets ? `<ul>${bullets}</ul>` : ''}
      </div>`;
    })
    .join('');

  const projetos = c.projetos
    .map((p) => {
      const titulo = p.link
        ? `<a href="${esc(p.link)}">${esc(p.nome)}</a>`
        : esc(p.nome);
      const stack = p.stack.length
        ? `<p class="proj-stack">${p.stack.map(esc).join('  ·  ')}</p>`
        : '';
      return `<div class="item">
        <div class="item-titulo">${titulo}</div>
        ${p.descricao ? `<p class="proj-desc">${esc(p.descricao)}</p>` : ''}
        ${stack}
      </div>`;
    })
    .join('');

  const formacao = c.formacao
    .map((f) => {
      const head = [esc(f.instituicao), esc(f.curso)].filter(Boolean).join(' · ');
      return `<div class="item">
        <div class="item-head"><span class="item-titulo">${head}</span>${
          f.periodo ? `<span class="item-per">${esc(f.periodo)}</span>` : ''
        }</div>
      </div>`;
    })
    .join('');

  const secao = (titulo: string, corpo: string) =>
    corpo ? `<section><h2>${titulo}</h2>${corpo}</section>` : '';

  return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8" />
<title>${esc(nomeArquivoPdf(c.nome, vagaTitulo))}</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    font-family: Arial, Helvetica, sans-serif;
    color: #1a1a1a; font-size: 10.5pt; line-height: 1.4;
    margin: 0; padding: 13mm 15mm;
  }
  h1 { font-size: 22pt; margin: 0 0 2px; font-weight: 700; }
  .headline { font-size: 12pt; color: #444; margin: 0 0 6px; }
  .contato { font-size: 9.5pt; color: #333; margin: 0; }
  section { margin-top: 18px; }
  h2 {
    font-size: 11pt; text-transform: uppercase; letter-spacing: .06em;
    margin: 0 0 8px; padding-bottom: 3px; border-bottom: 1px solid #999;
  }
  p { margin: 0 0 6px; }
  .comp { display: flex; gap: 10px; margin: 0 0 4px; }
  .comp-cat { font-weight: 700; flex: 0 0 142px; }
  .comp-itens { flex: 1; }
  .item { margin-bottom: 10px; }
  .item-head { display: flex; justify-content: space-between; gap: 12px; }
  .item-titulo { font-weight: 700; }
  .item-per { color: #555; white-space: nowrap; font-size: 9.5pt; }
  .proj-stack { color: #555; font-size: 9.5pt; margin: 2px 0 0; }
  .proj-desc { margin: 2px 0 0; }
  a { color: #1a1a1a; }
  ul { margin: 4px 0 0; padding-left: 18px; }
  li { margin-bottom: 2px; }
  /* margem 0 no @page suprime o cabeçalho/rodapé do navegador
     (data, título, URL, nº de página); a margem real é o padding do body. */
  @page { margin: 0; }
  /* modo compacto: aperta espaçamentos pra puxar o conteúdo pra 1 página */
  body.compact { line-height: 1.32; padding: 10mm 14mm; }
  body.compact h1 { font-size: 20pt; }
  body.compact section { margin-top: 11px; }
  body.compact h2 { margin-bottom: 6px; }
  body.compact .item { margin-bottom: 7px; }
  body.compact .comp { margin-bottom: 3px; }
  body.compact ul { margin-top: 2px; }
  body.compact li { margin-bottom: 1px; }
</style></head>
<body>
  <header>
    <h1>${esc(c.nome)}</h1>
    ${c.titulo ? `<p class="headline">${esc(c.titulo)}</p>` : ''}
    ${linhaContato(c.contato) ? `<p class="contato">${linhaContato(c.contato)}</p>` : ''}
  </header>
  ${c.resumo ? secao('Resumo', `<p>${esc(c.resumo)}</p>`) : ''}
  ${secao('Competências', competencias)}
  ${secao('Experiência Profissional', experiencias)}
  ${secao('Projetos', projetos)}
  ${secao('Formação', formacao)}
</body></html>`;
}

/**
 * Encolhe o conteúdo pra caber em 1 página quando falta pouco; deixa fluir em
 * 2 páginas só quando o conteúdo é grande de verdade (passaria da metade da 2ª
 * mesmo já compactado). ATS lê o texto igual — zoom não vira imagem.
 */
function ajustarParaUmaPagina(doc: Document) {
  const PX_POR_MM = 96 / 25.4;
  const alturaPagina = 297 * PX_POR_MM; // A4 em px (CSS)
  const body = doc.body;
  const altura = () => doc.documentElement.scrollHeight;

  if (altura() <= alturaPagina) return; // já cabe

  body.classList.add('compact');
  const h = altura();
  if (h <= alturaPagina) return; // o modo compacto resolveu

  const zoom = (alturaPagina / h) * 0.98;
  // só encolhe se o texto ainda fica legível (~72%); senão, vão 2 páginas
  if (zoom >= 0.72) {
    (body.style as unknown as { zoom: string }).zoom = String(zoom);
  }
}

/**
 * Imprime o currículo via iframe oculto (sem popup, sem travar a página).
 * Dispara o diálogo UMA vez só e remove o iframe depois.
 */
function imprimir(c: CurriculoVaga, vagaTitulo?: string | null) {
  const iframe = document.createElement('iframe');
  iframe.setAttribute('aria-hidden', 'true');
  // precisa de largura A4 real (offscreen) pra medir a altura como no print
  iframe.style.cssText =
    'position:fixed;left:-9999px;top:0;width:210mm;height:297mm;border:0;';
  document.body.appendChild(iframe);

  const win = iframe.contentWindow;
  const doc = win?.document;
  if (!win || !doc) {
    iframe.remove();
    return;
  }
  doc.open();
  doc.write(curriculoHtml(c, vagaTitulo));
  doc.close();

  // O "Salvar como PDF" sugere o nome a partir do <title> da PÁGINA principal
  // (não do iframe). Troca temporariamente e restaura depois de imprimir.
  const nomeArquivo = nomeArquivoPdf(c.nome, vagaTitulo);
  const tituloOriginal = document.title;

  let feito = false;
  const imprimirUmaVez = () => {
    if (feito) return;
    feito = true;
    try {
      ajustarParaUmaPagina(doc);
      document.title = nomeArquivo;
      win.focus();
      win.print();
    } finally {
      // restaura o título e tira o iframe depois que o diálogo fecha
      setTimeout(() => {
        document.title = tituloOriginal;
        iframe.remove();
      }, 1000);
    }
  };

  iframe.onload = imprimirUmaVez;
  // fallback se o onload não disparar após o document.write
  setTimeout(imprimirUmaVez, 600);
}

export function CurriculoPdf({
  curriculo,
  vagaTitulo,
}: {
  curriculo: CurriculoVaga;
  vagaTitulo?: string | null;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between gap-3 flex-wrap mb-4">
        <h4 className="font-display font-semibold text-sm text-ink m-0">
          Currículo ATS — sob medida pra esta vaga
        </h4>
        <button
          type="button"
          className="btn-primary"
          onClick={() => imprimir(curriculo, vagaTitulo)}
        >
          Baixar PDF (imprimir)
        </button>
      </div>

      {/* Prévia fiel ao PDF */}
      <div className="curriculo-preview border border-line rounded bg-white text-ink p-6 text-[13px] leading-relaxed">
        <div className="font-display font-bold text-2xl">{curriculo.nome}</div>
        {curriculo.titulo && (
          <div className="text-ink-soft mt-0.5">{curriculo.titulo}</div>
        )}
        {curriculo.contato && (
          <div className="text-[12px] text-ink-mute mt-1">
            {[
              curriculo.contato.email,
              curriculo.contato.telefone,
              curriculo.contato.linkedin,
              curriculo.contato.github,
              curriculo.contato.portfolio,
            ]
              .filter(Boolean)
              .join('  ·  ')}
          </div>
        )}

        {curriculo.resumo && (
          <PreviewSecao titulo="Resumo">
            <p className="m-0">{curriculo.resumo}</p>
          </PreviewSecao>
        )}

        {curriculo.competencias.some((g) => g.itens.length) && (
          <PreviewSecao titulo="Competências">
            {curriculo.competencias
              .filter((g) => g.itens.length)
              .map((g) => (
                <div key={g.categoria} className="flex gap-2.5 mb-1">
                  <span className="font-semibold flex-none w-[142px]">
                    {g.categoria}
                  </span>
                  <span className="flex-1">{g.itens.join('  ·  ')}</span>
                </div>
              ))}
          </PreviewSecao>
        )}

        {curriculo.experiencias.length > 0 && (
          <PreviewSecao titulo="Experiência Profissional">
            {curriculo.experiencias.map((e, i) => (
              <div key={i} className="mb-2.5">
                <div className="flex justify-between gap-3">
                  <span className="font-semibold">
                    {[e.cargo, e.empresa].filter(Boolean).join(' · ')}
                  </span>
                  {e.periodo && (
                    <span className="text-ink-mute text-[12px] whitespace-nowrap">
                      {e.periodo}
                    </span>
                  )}
                </div>
                {e.bullets.length > 0 && (
                  <ul className="mt-1 mb-0 pl-5 list-disc">
                    {e.bullets.map((b, j) => (
                      <li key={j}>{b}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </PreviewSecao>
        )}

        {curriculo.projetos.length > 0 && (
          <PreviewSecao titulo="Projetos">
            {curriculo.projetos.map((p, i) => (
              <div key={i} className="mb-2.5">
                <div className="font-semibold">{p.nome}</div>
                {p.descricao && <p className="m-0 mt-0.5">{p.descricao}</p>}
                {p.stack.length > 0 && (
                  <p className="m-0 mt-0.5 text-ink-mute text-[12px]">
                    {p.stack.join('  ·  ')}
                  </p>
                )}
              </div>
            ))}
          </PreviewSecao>
        )}

        {curriculo.formacao.length > 0 && (
          <PreviewSecao titulo="Formação">
            {curriculo.formacao.map((f, i) => (
              <div key={i} className="flex justify-between gap-3 mb-1">
                <span className="font-semibold">
                  {[f.instituicao, f.curso].filter(Boolean).join(' · ')}
                </span>
                {f.periodo && (
                  <span className="text-ink-mute text-[12px] whitespace-nowrap">
                    {f.periodo}
                  </span>
                )}
              </div>
            ))}
          </PreviewSecao>
        )}
      </div>

      <p className="text-[11px] text-ink-mute mt-3">
        Coluna única, fonte padrão e termos espelhados da vaga — feito pra
        passar no ATS. Revise antes de enviar.
      </p>
    </div>
  );
}

function PreviewSecao({
  titulo,
  children,
}: {
  titulo: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-4">
      <h5 className="font-semibold uppercase tracking-[0.06em] text-[11px] text-ink border-b border-line pb-1 mb-2 m-0">
        {titulo}
      </h5>
      {children}
    </section>
  );
}
