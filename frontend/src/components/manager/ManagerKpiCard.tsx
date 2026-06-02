import { formatBrl, formatNumberPtBr } from '../../lib/format'

export interface ManagerKpiCardProps {
  label: string
  value: string
  subtitle?: string
  deltaPct?: number | null
  previousLabel?: string
}

function DeltaBadge({ delta }: { delta: number }) {
  const positive = delta >= 0
  return (
    <span
      className={[
        'ml-2 text-xs font-medium tabular-nums',
        positive ? 'text-emerald-700' : 'text-red-700',
      ].join(' ')}
    >
      {positive ? '+' : ''}
      {delta.toFixed(1)}%
    </span>
  )
}

export function ManagerKpiCard({
  label,
  value,
  subtitle,
  deltaPct,
  previousLabel,
}: ManagerKpiCardProps) {
  return (
    <article className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-4 shadow-[0_1px_2px_rgba(0,0,0,0.04)]">
      <p className="text-xs text-[var(--text-secondary)]">{label}</p>
      <p className="mt-2 flex flex-wrap items-baseline gap-1 text-2xl font-semibold tabular-nums text-[var(--text-primary)]">
        {value}
        {deltaPct != null ? <DeltaBadge delta={deltaPct} /> : null}
      </p>
      {subtitle ? (
        <p className="mt-1 text-xs text-[var(--text-secondary)]">{subtitle}</p>
      ) : null}
      {previousLabel ? (
        <p className="mt-1 text-xs text-[var(--text-tertiary)]">{previousLabel}</p>
      ) : null}
    </article>
  )
}

export function formatCostValue(
  cost: number | null | undefined,
  hasRates: boolean,
): string {
  if (!hasRates || cost == null) {
    return '—'
  }
  return formatBrl(cost)
}

export function formatPagesSubtitle(mono: number, color: number): string {
  return `${formatNumberPtBr(mono)} mono · ${formatNumberPtBr(color)} color`
}
