import { baseUrl } from '../../api/client'
import { useUrlFilters } from '../../hooks/useUrlFilters'
import type { ExportFilters, JobFilters } from '../../types/api'
import { Button } from '../ui/Button'

function toExportFilters(filters: JobFilters): ExportFilters {
  const { page: _page, size: _size, ...exportFilters } = filters
  return exportFilters
}

function exportFiltersToSearchParams(filters: ExportFilters): URLSearchParams {
  const params = new URLSearchParams()
  if (filters.date_from) params.set('date_from', filters.date_from)
  if (filters.date_to) params.set('date_to', filters.date_to)
  const username = filters.username?.trim()
  if (username) params.set('username', username)
  const printer = filters.printer?.trim()
  if (printer) params.set('printer', printer)
  const search = filters.search?.trim()
  if (search) params.set('search', search)
  return params
}

function chargebackUrl(path: string, filters: ExportFilters): string {
  const qs = exportFiltersToSearchParams(filters).toString()
  return `${baseUrl}${path}${qs ? `?${qs}` : ''}`
}

export function ChargebackExportButtons() {
  const { filters } = useUrlFilters()
  const exportFilters = toExportFilters(filters)

  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <Button
        variant="secondary"
        onClick={() => {
          window.open(
            chargebackUrl('/export/chargeback/by-cost-center', exportFilters),
            '_blank',
            'noopener,noreferrer',
          )
        }}
      >
        Exportar chargeback (CC)
      </Button>
      <Button
        variant="secondary"
        onClick={() => {
          window.open(
            chargebackUrl('/export/chargeback/by-department', exportFilters),
            '_blank',
            'noopener,noreferrer',
          )
        }}
      >
        Exportar chargeback (Departamento)
      </Button>
    </div>
  )
}
