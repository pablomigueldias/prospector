interface StatCardProps {
  label: string;
  value: string | number;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  loading?: boolean;
}

export function StatCard({
  label,
  value,
  trend,
  trendDirection = 'neutral',
  loading,
}: StatCardProps) {
  return (
    <div className="card p-4">
      <div className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute mb-2">
        {label}
      </div>
      <div className="font-display font-semibold tracking-tight text-2xl text-ink leading-none">
        {loading ? (
          <div className="h-6 w-12 bg-line-soft rounded animate-pulse" />
        ) : (
          value
        )}
      </div>
      {trend && !loading && (
        <div
          className={[
            'text-[11px] mt-1',
            trendDirection === 'up' && 'text-success',
            trendDirection === 'down' && 'text-brand-deep',
            trendDirection === 'neutral' && 'text-ink-mute',
          ]
            .filter(Boolean)
            .join(' ')}
        >
          {trend}
        </div>
      )}
    </div>
  );
}
