import { useState } from 'react';

/**
 * Botão "copiar linha digitável" do boleto — copia só os dígitos pro
 * clipboard e mostra um "copiado!" por uns segundos. Pra pagar no banco sem
 * digitar.
 */
export function CopiarLinha({ linha }: { linha: string }) {
  const [copiado, setCopiado] = useState(false);

  async function copiar() {
    try {
      await navigator.clipboard.writeText(linha);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      /* clipboard indisponível (http/permite) — ignora silenciosamente */
    }
  }

  return (
    <button
      type="button"
      onClick={copiar}
      title={`Copiar linha digitável: ${linha}`}
      className="inline-flex items-center gap-1 text-[10.5px] text-ink-soft hover:text-brand transition-colors"
    >
      <span aria-hidden>{copiado ? '✓' : '⧉'}</span>
      {copiado ? 'copiado!' : 'copiar código'}
    </button>
  );
}
