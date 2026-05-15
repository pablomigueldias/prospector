import {
  IconBuildingHospital,
  IconBuildingStore,
  IconCheck,
  IconCode,
  IconInbox,
  IconTruck,
} from './Icon';
import type { LeadHistoryItem } from '@/lib/types';

interface LeadRowProps {
  item: LeadHistoryItem;
}

export function LeadRow({ item }: LeadRowProps) {
  const SetorIcon = iconForSetor(item.setor);
  const subtitle = [item.cnpj, item.setor, formatCidadeUf(item)]
    .filter(Boolean)
    .join(' · ');

  return (
    <div className="card p-3.5 px-[18px] grid grid-cols-[auto_1fr_auto_auto] gap-4 items-center">
      <div className="w-9 h-9 rounded bg-bg-alt flex items-center justify-center text-ink-soft">
        <SetorIcon className="text-lg" />
      </div>

      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-sm font-medium text-ink truncate">
          {item.empresa_nome}
        </span>
        <span className="font-mono text-[11.5px] text-ink-mute truncate">
          {subtitle || '—'}
        </span>
      </div>

      <div className="flex items-center gap-1.5 text-xs text-ink-soft">
        <IconCheck className="text-success text-sm" />
        <span>No Notion</span>
      </div>

      <span className="font-mono text-[11.5px] text-ink-faint whitespace-nowrap">
        {formatRelativeTime(item.enviado_em)}
      </span>
    </div>
  );
}

interface LeadHistoryListProps {
  items: LeadHistoryItem[];
  loading: boolean;
  error: { message: string } | null;
}

export function LeadHistoryList({
  items,
  loading,
  error,
}: LeadHistoryListProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card p-3.5 h-[68px] animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-6 text-center">
        <p className="text-sm text-ink-mute">
          Não consegui carregar o histórico:{' '}
          <span className="text-ink">{error.message}</span>
        </p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="card p-8 text-center flex flex-col items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-bg-alt flex items-center justify-center text-ink-mute">
          <IconInbox className="text-xl" />
        </div>
        <div>
          <h3 className="font-display font-semibold text-base text-ink mb-1">
            Sem leads ainda
          </h3>
          <p className="text-sm text-ink-mute max-w-md">
            Quando você prospectar a primeira empresa, ela aparece aqui.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {items.map((item) => (
        <LeadRow key={item.arquivo} item={item} />
      ))}
    </div>
  );
}


function iconForSetor(setor: string | null) {
  if (!setor) return IconBuildingStore;
  const s = setor.toLowerCase();
  if (s.includes('saúde') || s.includes('saude') || s.includes('médic'))
    return IconBuildingHospital;
  if (s.includes('tech') || s.includes('tecno') || s.includes('software'))
    return IconCode;
  if (s.includes('logíst') || s.includes('logist') || s.includes('transport'))
    return IconTruck;
  return IconBuildingStore;
}

function formatCidadeUf(item: LeadHistoryItem): string {
  if (item.cidade && item.estado) return `${item.cidade}/${item.estado}`;
  if (item.cidade) return item.cidade;
  if (item.estado) return item.estado;
  return '';
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';

  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);

  if (diffMin < 1) return 'agora';
  if (diffMin < 60) return `há ${diffMin} min`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `há ${diffHours}h`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `há ${diffDays}d`;
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
}
