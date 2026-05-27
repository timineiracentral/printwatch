import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchTiExport, tiExportCsvUrl } from '../../api/settings/users'
import { Button } from '../../components/ui/Button'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import { Skeleton } from '../../components/ui/Skeleton'

export function TiExportPage() {
  const { userId } = useParams<{ userId: string }>()
  const id = userId ? Number(userId) : NaN
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['ti-export', id],
    queryFn: () => fetchTiExport(id),
    enabled: Number.isFinite(id),
  })

  const titleName = data?.[0]?.display_name ?? 'Usuário'

  return (
    <div className="min-h-screen bg-white p-8 text-[var(--text-primary)] print:p-4">
      <div className="mb-6 flex flex-wrap items-center gap-3 print:hidden">
        <Link to="/settings/users" className="text-sm text-[var(--accent)] underline">
          ← Voltar para usuários
        </Link>
        <Button type="button" variant="secondary" onClick={() => window.print()}>
          Imprimir
        </Button>
        <a
          href={tiExportCsvUrl(id)}
          className="inline-flex min-h-10 items-center rounded-lg border border-[var(--border-subtle)] px-4 text-sm"
          download
        >
          Baixar CSV
        </a>
      </div>

      <h1 className="mb-4 text-xl font-semibold">
        Roteiro de instalação — {titleName}
      </h1>

      {isError ? (
        <ErrorBanner message="Erro ao carregar roteiro." onRetry={() => void refetch()} />
      ) : isLoading ? (
        <Skeleton className="h-32 w-full" />
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b">
              {[
                'Impressora',
                'Fila no servidor',
                'URL IPP',
                'Padrão',
                'Departamento',
                'Local',
              ].map((h) => (
                <th key={h} className="px-2 py-2 text-left font-medium">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((row) => (
              <tr key={`${row.cups_queue_name}-${row.printer_display_name}`} className="border-b">
                <td className="px-2 py-2">{row.printer_display_name}</td>
                <td className="px-2 py-2 font-mono text-xs">{row.cups_queue_name}</td>
                <td className="px-2 py-2 font-mono text-xs">{row.ipp_url ?? '—'}</td>
                <td className="px-2 py-2">{row.is_default ? 'Sim' : 'Não'}</td>
                <td className="px-2 py-2">{row.department ?? '—'}</td>
                <td className="px-2 py-2">{row.location ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
