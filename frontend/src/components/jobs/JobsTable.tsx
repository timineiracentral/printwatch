import { FileQuestion, Pencil } from 'lucide-react'
import { useState } from 'react'
import { useFleetStatusMap } from '../../hooks/useFleetStatusMap'
import { useJobs } from '../../hooks/useJobs'
import { useShowCostColumn } from '../../hooks/useShowCostColumn'
import { useUrlFilters } from '../../hooks/useUrlFilters'
import { formatBrl, formatDateTime, formatNumberPtBr } from '../../lib/format'
import { hasActiveFilters } from '../../lib/filters'
import { formatMediaLabel } from '../../lib/media'
import { ErrorBanner } from '../ui/ErrorBanner'
import { EmptyState } from '../ui/EmptyState'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Skeleton } from '../ui/Skeleton'
import type { JobOut } from '../../types/api'
import { ColorModeCorrectionModal } from './ColorModeCorrectionModal'

const ERROR_MESSAGE =
  'Não foi possível carregar os dados. Verifique se o servidor está online e tente novamente.'

function TableRowSkeleton({ columns }: { columns: number }) {
  return (
    <tr className="border-b border-[var(--border-subtle)]">
      {Array.from({ length: columns }, (_, i) => (
        <td key={i} className="px-3 py-2">
          <Skeleton className="h-4 w-full max-w-[120px]" />
        </td>
      ))}
    </tr>
  )
}

function formatEstimatedCost(cost: number | null | undefined): string {
  if (cost == null) return '—'
  return formatBrl(cost)
}

export function JobsTable() {
  const { filters, clearFilters } = useUrlFilters()
  const { showCostColumn, setShowCostColumn } = useShowCostColumn()
  const { data, isLoading, isFetching, isError, refetch } = useJobs(filters)
  const fleetStatusMap = useFleetStatusMap()
  const [correctionJob, setCorrectionJob] = useState<JobOut | null>(null)
  const isRefetching = isFetching && !isLoading
  const activeFilters = hasActiveFilters(filters)

  const baseHeaders = [
    'Data/Hora',
    'Usuário',
    'Impressora',
    'Arquivo',
    'Páginas',
    'Papel',
    'Origem',
  ]
  const headers = showCostColumn
    ? [...baseHeaders.slice(0, 5), 'Custo est.', ...baseHeaders.slice(5)]
    : baseHeaders
  const columnCount = headers.length

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
    <>
      <div className="mb-2 flex justify-end">
        <label className="flex cursor-pointer items-center gap-2 text-sm text-[var(--text-secondary)]">
          <input
            type="checkbox"
            className="size-4 rounded border-[var(--border)]"
            checked={showCostColumn}
            onChange={(e) => setShowCostColumn(e.target.checked)}
          />
          Exibir custo estimado
        </label>
      </div>

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
                    {headers.map((label, i) => (
                      <th
                        key={label}
                        scope="col"
                        className={[
                          'px-3 py-2.5 text-left text-xs font-medium text-[var(--text-secondary)]',
                          label === 'Páginas' || label === 'Custo est.' ? 'text-right' : '',
                          i === 0 ? 'w-[140px]' : '',
                          label === 'Páginas' ? 'w-[72px]' : '',
                        ]
                          .filter(Boolean)
                          .join(' ')}
                      >
                        {label}
                      </th>
                    ))}
                    <th scope="col" className="w-[100px] px-3 py-2.5 text-xs font-medium text-[var(--text-secondary)]">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading
                    ? Array.from({ length: 8 }, (_, i) => (
                        <TableRowSkeleton key={i} columns={columnCount + 1} />
                      ))
                    : items.map((job, index) => {
                        const pending = (job.pages_pending_color ?? 0) > 0
                        const hasManual = job.has_manual_correction === true
                        const showCorrection =
                          (pending || hasManual) && job.minute_bucket != null
                        const fleetStatus =
                          job.printer_id != null
                            ? fleetStatusMap.get(job.printer_id)
                            : undefined
                        return (
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
                              <span className="block truncate" title={job.username}>
                                {job.username}
                              </span>
                            </td>
                            <td className="max-w-[180px] px-3 py-2">
                              <div className="flex flex-wrap items-center gap-1">
                                <span className="block truncate" title={job.printer}>
                                  {job.printer}
                                </span>
                                {fleetStatus === 'offline' ? (
                                  <Badge variant="warning" title="Impressora offline">
                                    Offline
                                  </Badge>
                                ) : null}
                                {fleetStatus === 'unknown' ? (
                                  <Badge variant="muted" title="Status de frota desconhecido">
                                    Desconhecido
                                  </Badge>
                                ) : null}
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
                              <div className="flex flex-col items-end gap-0.5">
                                <span>{formatNumberPtBr(job.pages)}</span>
                                {pending ? (
                                  <Badge variant="warning" title="Páginas sem modo de cor">
                                    {`${formatNumberPtBr(job.pages_pending_color!)} pendente${(job.pages_pending_color ?? 0) === 1 ? '' : 's'}`}
                                  </Badge>
                                ) : null}
                                {hasManual ? (
                                  <span
                                    className="inline-flex items-center gap-0.5"
                                    title="Contém correção manual de modo de cor"
                                  >
                                    <Pencil
                                      className="size-3 text-[var(--text-secondary)]"
                                      aria-hidden
                                    />
                                    <Badge
                                      variant="muted"
                                      title="Contém correção manual de modo de cor"
                                    >
                                      Corrigido
                                    </Badge>
                                  </span>
                                ) : null}
                              </div>
                            </td>
                            {showCostColumn ? (
                              <td className="whitespace-nowrap px-3 py-2 text-right tabular-nums">
                                {formatEstimatedCost(job.estimated_cost)}
                              </td>
                            ) : null}
                            <td className="px-3 py-2">
                              {formatMediaLabel(job.media) || '—'}
                            </td>
                            <td className="px-3 py-2 text-[var(--text-secondary)]">
                              {job.host_origin ?? '—'}
                            </td>
                            <td className="px-3 py-2">
                              {showCorrection ? (
                                <Button
                                  variant="ghost"
                                  className="min-h-8 px-2 text-xs"
                                  onClick={() => setCorrectionJob(job)}
                                >
                                  Corrigir cor
                                </Button>
                              ) : null}
                            </td>
                          </tr>
                        )
                      })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <ColorModeCorrectionModal
        job={correctionJob}
        open={correctionJob != null}
        onClose={() => setCorrectionJob(null)}
      />
    </>
  )
}
