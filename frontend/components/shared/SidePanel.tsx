import { useEffect, type ReactNode } from 'react';

interface SidePanelProps {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  children: ReactNode;
  /** Ações no canto direito do cabeçalho (ex: botão Editar). */
  acoes?: ReactNode;
  /** Largura máxima do painel (default xl). */
  width?: string;
}

/**
 * Painel lateral (drawer) deslizando da direita — estilo Notion. Mais espaço que
 * o Modal centralizado, ocupa a altura toda e rola o conteúdo. Fecha no Esc e no
 * clique fora. Usado pelas fichas/registros do CRM.
 */
export function SidePanel({
  open,
  onClose,
  title,
  children,
  acoes,
  width = 'max-w-2xl',
}: SidePanelProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-ink/30 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className={`bg-surface h-full w-full ${width} shadow-2xl flex flex-col animate-[painel_.18s_ease-out]`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 px-7 pt-5 pb-4 border-b border-line sticky top-0 bg-surface z-10">
          <h3 className="font-display font-semibold text-xl tracking-tight text-ink m-0 leading-snug">
            {title}
          </h3>
          <div className="flex items-center gap-2 shrink-0">
            {acoes}
            <button
              type="button"
              onClick={onClose}
              className="text-ink-mute hover:text-ink text-2xl leading-none px-1"
              aria-label="Fechar"
            >
              ×
            </button>
          </div>
        </div>
        <div className="px-7 py-5 overflow-y-auto grow">{children}</div>
      </div>
    </div>
  );
}
