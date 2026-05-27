export type SummaryCardVariant = 'metric' | 'top'

export interface SummaryCardProps {
  variant: SummaryCardVariant
  label: string
  /** Valor numérico (metric) ou linha formatada (top). */
  value?: string
  /** Quando true, exibe copy de vazio no lugar do valor (tops sem entrada). */
  isEmpty?: boolean
  emptyText?: string
}

export function SummaryCard({
  variant,
  label,
  value,
  isEmpty = false,
  emptyText = 'Sem dados no período',
}: SummaryCardProps) {
  const displayValue = isEmpty ? emptyText : value

  return (
    <article
      className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-4 shadow-[0_1px_2px_rgba(0,0,0,0.04)]"
    >
      <p className="text-xs text-[var(--text-secondary)]">{label}</p>
      {variant === 'metric' ? (
        <p
          className={[
            'mt-2 text-2xl font-semibold leading-tight tabular-nums',
            isEmpty ? 'text-[var(--text-secondary)]' : 'text-[var(--text-primary)]',
          ].join(' ')}
        >
          {displayValue}
        </p>
      ) : (
        <p
          className={[
            'mt-2 text-sm leading-snug',
            isEmpty ? 'text-[var(--text-secondary)]' : 'text-[var(--text-primary)]',
          ].join(' ')}
        >
          {displayValue}
        </p>
      )}
    </article>
  )
}
