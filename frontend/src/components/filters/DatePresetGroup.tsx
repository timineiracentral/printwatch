import {
  presetLast7Days,
  presetMonthToDate,
  presetToday,
} from '../../lib/dates'
import type { JobFilters } from '../../types/api'
import type { DatePresetName } from '../../hooks/useUrlFilters'

const PRESETS: { name: DatePresetName; label: string }[] = [
  { name: 'today', label: 'Hoje' },
  { name: 'last7', label: 'Últimos 7 dias' },
  { name: 'month', label: 'Mês atual' },
]

function presetMatches(filters: JobFilters, name: DatePresetName): boolean {
  const expected =
    name === 'today'
      ? presetToday()
      : name === 'last7'
        ? presetLast7Days()
        : presetMonthToDate()
  return (
    filters.date_from === expected.date_from &&
    filters.date_to === expected.date_to
  )
}

export interface DatePresetGroupProps {
  filters: JobFilters
  onPreset: (name: DatePresetName) => void
}

export function DatePresetGroup({ filters, onPreset }: DatePresetGroupProps) {
  return (
    <div
      className="inline-flex rounded-lg border border-[var(--border)] bg-[var(--bg-canvas)] p-0.5"
      role="group"
      aria-label="Período rápido"
    >
      {PRESETS.map(({ name, label }) => {
        const active = presetMatches(filters, name)
        return (
          <button
            key={name}
            type="button"
            onClick={() => onPreset(name)}
            className={[
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150',
              'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]',
              active
                ? 'bg-[var(--accent-tint)] text-[var(--accent)]'
                : 'text-[var(--text-secondary)] hover:bg-[var(--row-hover)] hover:text-[var(--text-primary)]',
            ]
              .filter(Boolean)
              .join(' ')}
            aria-pressed={active}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
