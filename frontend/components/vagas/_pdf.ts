// Helpers compartilhados pra gerar PDF (currículo e carta) via "imprimir → Salvar
// como PDF", sem dependência extra. O nome sugerido do arquivo vem do <title> da
// PÁGINA principal (o Chrome ignora o title do iframe), então a impressão troca o
// document.title temporariamente.

/** Vira "Pablo Dias" → "pablo-dias" (sem acento, minúsculo, hífen). */
export const slug = (s?: string | null): string =>
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
export const slugNome = (s?: string | null): string => {
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

/** Escapa texto pra interpolar em HTML. */
export const esc = (s?: string | null): string =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

/**
 * Imprime um documento HTML via iframe oculto (sem popup, sem travar a página).
 * Dispara o diálogo UMA vez e remove o iframe depois. `nomeArquivo` vira o nome
 * sugerido no "Salvar como PDF" (via document.title da página). `ajustar` é um
 * hook opcional pra mexer no doc antes de imprimir (ex.: encolher pra 1 página).
 */
export function imprimirDocumento(
  html: string,
  nomeArquivo: string,
  ajustar?: (doc: Document) => void,
): void {
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
  doc.write(html);
  doc.close();

  const tituloOriginal = document.title;

  let feito = false;
  const imprimirUmaVez = () => {
    if (feito) return;
    feito = true;
    try {
      ajustar?.(doc);
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
