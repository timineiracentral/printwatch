import { useState } from 'react'
import { downloadCsv, ExportCapError } from '../../api/export'
import { useUrlFilters } from '../../hooks/useUrlFilters'
import type { ExportFilters, JobFilters } from '../../types/api'
import { Button } from '../ui/Button'
import { ErrorBanner } from '../ui/ErrorBanner'

function toExportFilters(filters: JobFilters): ExportFilters {
  const { page: _page, size: _size, ...exportFilters } = filters
  return exportFilters
}

function formatBackendDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'object' && item !== null && 'msg' in item) {
          return String((item as { msg: unknown }).msg)
        }
        return String(item)
      })
      .join(' ')
  }
  if (typeof detail === 'object' && detail !== null && 'msg' in detail) {
    return String((detail as { msg: unknown }).msg)
  }
  return 'Limite de exportação excedido.'
}

export function ExportCsvButton() {
  const { filters } = useUrlFilters()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleExport() {
    setError(null)
    setLoading(true)
    try {
      await downloadCsv(toExportFilters(filters))
    } catch (err) {
      if (err instanceof ExportCapError) {
        setError(
          `${formatBackendDetail(err.detail)} Reduza o período ou adicione filtros.`,
        )
      } else {
        setError('Falha ao exportar. Verifique a conexão e tente novamente.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex max-w-md flex-col items-end gap-2">
      <Button
        variant="secondary"
        disabled={loading}
        onClick={() => void handleExport()}
        aria-busy={loading}
      >
        {loading ? 'Exportando…' : 'Exportar CSV'}
      </Button>
      {error ? (
        <ErrorBanner message={error} onRetry={() => void handleExport()} />
      ) : null}
    </div>
  )
}
