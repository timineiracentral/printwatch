import type { ManagerDatePreset } from '../../hooks/useUrlManagerFilters'
import type { ManagerFilters } from '../../types/api'
import { Button } from '../ui/Button'

const PRESETS: { id: ManagerDatePreset; label: string }[] = [
  { id: 'today', label: 'Hoje' },
  { id: 'last7', label: '7 dias' },
  { id: 'last30', label: '30 dias' },
  { id: 'last90', label: '90 dias' },
  { id: 'month', label: 'Mês atual' },
]

export interface ManagerFilterBarProps {
  filters: ManagerFilters
  onPreset: (preset: ManagerDatePreset) => void
  onCustomDates: (date_from: string, date_to: string) => void
}

export function ManagerFilterBar({
  filters,
  onPreset,
  onCustomDates,
}: ManagerFilterBarProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-4">
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((p) => (
          <Button
            key={p.id}
            type="button"
            variant={filters.preset === p.id ? 'primary' : 'secondary'}
            onClick={() => onPreset(p.id)}
          >
            {p.label}
          </Button>
        ))}
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs text-[var(--text-secondary)]">
          De
          <input
            type="date"
            className="rounded-lg border border-[var(--border)] px-2 py-1.5 text-sm"
            value={filters.date_from}
            onChange={(e) =>
              onCustomDates(e.target.value, filters.date_to)
            }
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-[var(--text-secondary)]">
          Até
          <input
            type="date"
            className="rounded-lg border border-[var(--border)] px-2 py-1.5 text-sm"
            value={filters.date_to}
            onChange={(e) =>
              onCustomDates(filters.date_from, e.target.value)
            }
          />
        </label>
      </div>
    </div>
  )
}
