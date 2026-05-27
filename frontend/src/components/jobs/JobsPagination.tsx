import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useJobs } from '../../hooks/useJobs'
import { useUrlFilters } from '../../hooks/useUrlFilters'
import { Button } from '../ui/Button'

const PAGE_SIZES = [50, 100] as const

export function JobsPagination() {
  const { filters, setFilters, setPage } = useUrlFilters()
  const { data, isLoading } = useJobs(filters)

  const total = data?.total ?? 0
  const page = data?.page ?? filters.page
  const size = data?.size ?? filters.size
  const totalPages = Math.max(1, Math.ceil(total / size))
  const from = total === 0 ? 0 : (page - 1) * size + 1
  const to = total === 0 ? 0 : Math.min(page * size, total)

  if (isLoading && !data) {
    return null
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 py-2">
      <p className="text-xs text-[var(--text-secondary)]">
        Mostrando {from}–{to} de {total} jobs
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
          Por página
          <select
            className="min-h-9 rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 text-sm text-[var(--text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]"
            value={size}
            onChange={(e) => {
              const next = Number.parseInt(e.target.value, 10)
              setFilters({ size: next, page: 1 })
            }}
            aria-label="Itens por página"
          >
            {PAGE_SIZES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>

        <div className="flex items-center gap-1">
          <Button
            variant="secondary"
            type="button"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            aria-label="Página anterior"
            className="min-h-9 px-2"
          >
            <ChevronLeft className="size-4" aria-hidden />
          </Button>
          <span className="min-w-[4rem] text-center text-xs text-[var(--text-secondary)]">
            {page} / {totalPages}
          </span>
          <Button
            variant="secondary"
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            aria-label="Próxima página"
            className="min-h-9 px-2"
          >
            <ChevronRight className="size-4" aria-hidden />
          </Button>
        </div>
      </div>
    </div>
  )
}
