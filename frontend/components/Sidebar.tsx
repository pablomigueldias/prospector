import Link from 'next/link';
import { useRouter } from 'next/router';

import { BrandMark } from './BrandMark';
import {
  IconChartBar,
  IconFromName,
  IconPlus,
  IconSettings,
} from './Icon';
import { useAgents } from '@/hooks/useAgents';
import { useAuth } from '@/contexts/AuthContext';
import { permissaoDoAgente } from '@/lib/permissions';
import type { Agent } from '@/lib/types';

// Ordem em que os grupos aparecem na sidebar. Categorias fora desta
// lista vão pro fim, em ordem alfabética.
const ORDEM_CATEGORIAS = ['Reative Systems', 'Pessoal'];

function ordenarCategorias(cats: string[]): string[] {
  return [...cats].sort((a, b) => {
    const ia = ORDEM_CATEGORIAS.indexOf(a);
    const ib = ORDEM_CATEGORIAS.indexOf(b);
    if (ia === -1 && ib === -1) return a.localeCompare(b);
    if (ia === -1) return 1;
    if (ib === -1) return -1;
    return ia - ib;
  });
}

export function Sidebar() {
  const { grouped, loading } = useAgents();
  const { usuario, logout, hasPermission } = useAuth();
  const router = useRouter();

  const currentSlug =
    typeof router.query.slug === 'string' ? router.query.slug : null;

  // UX: esconde agentes que o usuário não pode acessar (backend é quem trava).
  const podeVer = (agent: Agent) => {
    const need = permissaoDoAgente(agent.slug);
    return !need || hasPermission(need);
  };

  const categorias = ordenarCategorias(Object.keys(grouped));

  return (
    <aside className="flex flex-col gap-6 bg-surface border-r border-line p-5">
      <Link href="/" className="flex items-center gap-2.5 px-2">
        <span className="text-ink">
          <BrandMark size={28} />
        </span>
        <span className="font-display font-bold text-[15px] tracking-tight text-ink">
          Reative Systems
        </span>
      </Link>

      {loading && (
        <div>
          <div className="eyebrow mb-2 px-2">Agentes</div>
          <nav className="flex flex-col gap-0.5">
            <SidebarSkeleton />
            <SidebarSkeleton />
            <SidebarSkeleton />
          </nav>
        </div>
      )}

      {!loading &&
        categorias.map((categoria) => {
          const visiveis = grouped[categoria].filter(podeVer);
          if (visiveis.length === 0) return null;
          return (
            <div key={categoria}>
              <div className="eyebrow mb-2 px-2">{categoria}</div>
              <nav className="flex flex-col gap-0.5">
                {visiveis.map((agent) => (
                  <SidebarAgentItem
                    key={agent.slug}
                    agent={agent}
                    active={currentSlug === agent.slug}
                  />
                ))}
              </nav>
            </div>
          );
        })}

      <div>
        <div className="eyebrow mb-2 px-2">Workspace</div>
        <nav className="flex flex-col gap-0.5">
          {hasPermission('usuarios.gerenciar') && (
            <Link
              href="/admin/usuarios"
              className="flex items-center gap-2.5 px-2.5 py-2.5 rounded text-[13.5px] font-medium text-ink-soft hover:bg-bg-alt hover:text-ink transition-colors"
            >
              <span className="text-base text-ink-mute w-4">
                <IconSettings />
              </span>
              <span>Usuários</span>
            </Link>
          )}
          <SidebarStaticItem icon={<IconChartBar />} label="Métricas" disabled />
          <SidebarStaticItem icon={<IconSettings />} label="Conexões" disabled />
        </nav>
      </div>

      <div className="flex-1" />

      <button
        type="button"
        className="flex items-center gap-2 p-2.5 border border-dashed border-line rounded text-sm text-ink-mute transition-colors hover:border-brand hover:text-brand hover:bg-brand-soft/40"
      >
        <IconPlus className="text-sm" />
        <span>Novo agente</span>
      </button>

      <div className="flex items-center gap-2.5 p-2.5 bg-bg-alt rounded">
        <Link href="/conta" className="flex items-center gap-2.5 min-w-0 flex-1" title="Conta">
          <div className="w-8 h-8 rounded-full bg-ink text-white flex items-center justify-center font-display font-semibold text-[13px]">
            {(usuario?.nome ?? '?').charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[13px] font-medium text-ink truncate">
              {usuario?.nome ?? '—'}
            </div>
            <div className="text-[11px] text-ink-mute truncate">
              {usuario?.email ?? ''}
            </div>
          </div>
        </Link>
        <button
          type="button"
          onClick={() => void logout()}
          title="Sair"
          aria-label="Sair"
          className="text-[11px] font-medium text-ink-mute hover:text-brand transition-colors px-1.5 py-1"
        >
          Sair
        </button>
      </div>
    </aside>
  );
}


function SidebarAgentItem({ agent, active }: { agent: Agent; active: boolean }) {
  const isActive = agent.status === 'active';
  const content = (
    <div
      className={[
        'flex items-center gap-2.5 px-2.5 py-2.5 rounded text-[13.5px] font-medium transition-colors',
        active && 'bg-brand-soft text-brand-ink',
        !active && isActive && 'text-ink-soft hover:bg-bg-alt hover:text-ink',
        !isActive && 'text-ink-faint cursor-not-allowed',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <span
        className={[
          'w-[7px] h-[7px] rounded-full shrink-0',
          active ? 'bg-brand' : 'bg-line',
        ].join(' ')}
      />
      <span className="flex-1">{agent.name}</span>
      {!isActive && (
        <span className="text-[9px] font-mono uppercase tracking-[0.08em] text-ink-faint bg-bg-alt px-1.5 py-0.5 rounded-sm">
          soon
        </span>
      )}
    </div>
  );

  if (!isActive) {
    return <div aria-disabled>{content}</div>;
  }
  return <Link href={`/agents/${agent.slug}`}>{content}</Link>;
}

function SidebarStaticItem({
  icon,
  label,
  disabled,
}: {
  icon: React.ReactNode;
  label: string;
  disabled?: boolean;
}) {
  return (
    <div
      className={[
        'flex items-center gap-2.5 px-2.5 py-2.5 rounded text-[13.5px] font-medium transition-colors',
        disabled
          ? 'text-ink-faint cursor-not-allowed'
          : 'text-ink-soft hover:bg-bg-alt hover:text-ink cursor-pointer',
      ].join(' ')}
    >
      <span className="text-base text-ink-mute w-4">{icon}</span>
      <span>{label}</span>
    </div>
  );
}

function SidebarSkeleton() {
  return (
    <div className="flex items-center gap-2.5 px-2.5 py-2.5">
      <div className="w-[7px] h-[7px] rounded-full bg-line-soft animate-pulse" />
      <div className="h-3 bg-line-soft rounded animate-pulse flex-1" />
    </div>
  );
}
