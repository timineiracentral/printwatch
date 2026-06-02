import type { TonerDisplay } from '../../types/api'

export interface TonerBarProps {
  snmpEnabled: boolean
  toner?: TonerDisplay | null
}

function levelClass(pct: number): string {
  if (pct < 10) return 'bg-red-500'
  if (pct < 20) return 'bg-amber-500'
  return 'bg-emerald-600'
}

export function TonerBar({ snmpEnabled, toner }: TonerBarProps) {
  if (!snmpEnabled) {
    return <span className="text-sm text-[var(--text-tertiary)]">Não monitorado</span>
  }

  if (!toner || toner.status === 'unavailable') {
    return <span className="text-sm text-[var(--text-secondary)]">Indisponível</span>
  }

  const bars: { label: string; pct: number | null | undefined }[] = [
    { label: 'Preto', pct: toner.black_pct },
  ]
  if (toner.color_pct != null) {
    bars.push({ label: 'Color', pct: toner.color_pct })
  } else if (toner.partial_color) {
    bars.push({ label: 'Color', pct: null })
  }

  return (
    <div className="flex min-w-[140px] flex-col gap-1.5">
      {bars.map(({ label, pct }) =>
        pct == null ? (
          <span key={label} className="text-xs text-[var(--text-tertiary)]">
            {label}: —
          </span>
        ) : (
          <div key={label} className="flex items-center gap-2">
            <span className="w-10 shrink-0 text-xs text-[var(--text-secondary)]">{label}</span>
            <div
              className="h-2 min-w-[72px] flex-1 overflow-hidden rounded-full bg-[var(--bg-muted)]"
              role="progressbar"
              aria-valuenow={pct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Toner ${label}`}
            >
              <div
                className={`h-full rounded-full transition-all ${levelClass(pct)}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="w-8 text-right text-xs tabular-nums text-[var(--text-secondary)]">
              {pct}%
            </span>
          </div>
        ),
      )}
    </div>
  )
}
