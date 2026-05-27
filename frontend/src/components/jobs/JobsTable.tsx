import { FileQuestion } from 'lucide-react'
import { useJobs } from '../../hooks/useJobs'
import { useUrlFilters } from '../../hooks/useUrlFilters'
import { formatDateTime, formatNumberPtBr } from '../../lib/format'
import { hasActiveFilters } from '../../lib/filters'
import { formatMediaLabel } from '../../lib/media'
import { ErrorBanner } from '../ui/ErrorBanner'
import { EmptyState } from '../ui/EmptyState'
import { Badge } from '../ui/Badge'
import { Skeleton } from '../ui/Skeleton'

const ERROR_MESSAGE =
  'Não foi possível carregar os dados. Verifique se o servidor está online e tente novamente.'

function TableRowSkeleton() {
  return (
    <tr className="border-b border-[var(--border-subtle)]">
      {Array.from({ length: 7 }, (_, i) => (
        <td key={i} className="px-3 py-2">
          <Skeleton className="h-4 w-full max-w-[120px]" />
        </td>
      ))}
    </tr>
  )
}

export function JobsTable() {
  const { filters, clearFilters } = useUrlFilters()
  const { data, isLoading, isFetching, isError, refetch } = useJobs(filters)
  const isRefetching = isFetching && !isLoading
  const activeFilters = hasActiveFilters(filters)

  if (isError) {
    return (
      <ErrorBanner
        message={ERROR_MESSAGE}
        onRetry={() => {
          void refetch()
        }}
      />
    )
  }

  const items = data?.items ?? []
  const isEmpty = !isLoading && items.length === 0

  return (
    <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
      {isRefetching ? (
        <div
          className="absolute inset-x-0 top-0 z-10 h-0.5 overflow-hidden bg-[var(--border-subtle)]"
          role="progressbar"
          aria-label="Atualizando tabela"
        >
          <div className="table-progress-indeterminate h-full w-1/3 bg-[var(--accent)]" />
        </div>
      ) : null}

      <div
        className={[
          'flex min-h-0 flex-1 flex-col transition-opacity duration-150',
          isRefetching ? 'opacity-60' : 'opacity-100',
        ].join(' ')}
      >
        {isEmpty ? (
          activeFilters ? (
            <EmptyState
              heading="Nenhum job encontrado"
              body="Ajuste o período, usuário ou impressora e tente novamente."
              icon={<FileQuestion className="size-12" strokeWidth={1.25} />}
              actionLabel="Limpar filtros"
              onAction={clearFilters}
            />
          ) : (
            <EmptyState
              heading="Nenhum job registrado ainda"
              body="Os jobs aparecerão aqui após a primeira impressão."
              icon={<FileQuestion className="size-12" strokeWidth={1.25} />}
            />
          )
        ) : (
          <div className="min-h-0 flex-1 overflow-auto">
            <table className="w-full min-w-[800px] border-collapse text-sm">
              <thead className="sticky top-0 z-[1] bg-[var(--bg-surface)] shadow-[0_1px_0_var(--border-subtle)]">
                <tr>
                  {[
                    'Data/Hora',
                    'Usuário',
                    'Impressora',
                    'Arquivo',
                    'Páginas',
                    'Papel',
                    'Origem',
                  ].map((label, i) => (
                    <th
                      key={label}
                      scope="col"
                      className={[
                        'px-3 py-2.5 text-left text-xs font-medium text-[var(--text-secondary)]',
                        label === 'Páginas' ? 'text-right' : '',
                        i === 0 ? 'w-[140px]' : '',
                        i === 4 ? 'w-[72px]' : '',
                      ]
                        .filter(Boolean)
                        .join(' ')}
                    >
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? Array.from({ length: 8 }, (_, i) => <TableRowSkeleton key={i} />)
                  : items.map((job, index) => (
                      <tr
                        key={job.id ?? `${job.job_id}-${job.timestamp}`}
                        className={[
                          'min-h-10 border-b border-[var(--border-subtle)] transition-colors duration-150 hover:bg-[var(--row-hover)]',
                          index % 2 === 1 ? 'bg-[var(--row-stripe)]' : '',
                        ].join(' ')}
                      >
                        <td className="whitespace-nowrap px-3 py-2 text-[var(--text-primary)]">
                          {formatDateTime(job.timestamp)}
                        </td>
                        <td className="max-w-[160px] px-3 py-2">
                          <span
                            className="block truncate"
                            title={job.username}
                          >
                            {job.username}
                          </span>
                        </td>
                        <td className="max-w-[180px] px-3 py-2">
                          <div className="flex flex-wrap items-center gap-1">
                            <span className="block truncate" title={job.printer}>
                              {job.printer}
                            </span>
                            {job.outside_policy ? (
                              <Badge
                                variant="warning"
                                title="Usuário imprimiu em impressora não atribuída"
                              >
                                Fora da política
                              </Badge>
                            ) : null}
                          </div>
                        </td>
                        <td className="max-w-[240px] px-3 py-2">
                          <span
                            className="block truncate"
                            title={job.job_name ?? undefined}
                          >
                            {job.job_name ?? '—'}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-right tabular-nums">
                          {formatNumberPtBr(job.pages)}
                        </td>
                        <td className="px-3 py-2">
                          {formatMediaLabel(job.media) || '—'}
                        </td>
                        <td className="px-3 py-2 text-[var(--text-secondary)]">
                          {job.host_origin ?? '—'}
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
