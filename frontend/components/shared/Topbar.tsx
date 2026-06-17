import {
  IconBell,
  IconChevronRight,
  IconRobot,
  IconSearch,
} from '@/components/shared/Icon';

interface TopbarProps {
  currentAgentName?: string | null;
}

export function Topbar({ currentAgentName }: TopbarProps) {
  return (
    <header
      className="flex items-center justify-between px-8 py-4 border-b border-line backdrop-blur-nav"
      style={{ background: 'oklch(0.985 0.005 60 / 0.7)' }}
    >
      <nav className="flex items-center gap-2 text-[13px] text-ink-mute">
        <IconRobot className="text-base text-ink-mute" />
        <span>Agentes</span>
        {currentAgentName && (
          <>
            <IconChevronRight className="text-[14px] text-ink-faint" />
            <strong className="text-ink font-medium">{currentAgentName}</strong>
          </>
        )}
      </nav>

      <div className="flex items-center gap-2.5">
        <IconButton aria-label="Buscar">
          <IconSearch className="text-lg" />
        </IconButton>
        <IconButton aria-label="Notificações">
          <IconBell className="text-lg" />
        </IconButton>
      </div>
    </header>
  );
}

function IconButton({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className="w-9 h-9 rounded border border-line bg-surface text-ink-soft flex items-center justify-center transition-colors hover:border-ink-mute hover:text-ink"
      {...props}
    >
      {children}
    </button>
  );
}
