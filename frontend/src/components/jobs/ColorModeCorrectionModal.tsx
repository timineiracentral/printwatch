import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchJobLines, patchLineColorMode } from '../../api/jobs'
import { formatDateTime } from '../../lib/format'
import type { JobLineFilters, JobLineOut, JobOut } from '../../types/api'
import { ConfirmDialog } from '../settings/ConfirmDialog'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Dialog } from '../ui/Dialog'
import { ErrorBanner } from '../ui/ErrorBanner'
import { Skeleton } from '../ui/Skeleton'

export interface ColorModeCorrectionModalProps {
  job: JobOut | null
  open: boolean
  onClose: () => void
}

function jobToLineFilters(job: JobOut): JobLineFilters | null {
  if (!job.minute_bucket) return null
  return {
    printer: job.printer,
    username: job.username,
    job_id: job.job_id,
    job_name: job.job_name ?? null,
    minute_bucket: job.minute_bucket,
  }
}

function sourceLabel(source: string | null | undefined): string {
  if (source === 'captured') return 'Capturado'
  if (source === 'manual') return 'Manual'
  if (source === 'mono_only') return 'Heurística'
  return 'Pendente'
}

function sourceBadgeVariant(
  source: string | null | undefined,
): 'default' | 'muted' | 'warning' {
  if (source === 'manual') return 'default'
  if (source === 'captured') return 'muted'
  if (source === 'mono_only') return 'muted'
  return 'warning'
}

function isPendingLine(line: JobLineOut): boolean {
  return line.color_mode == null
}

function colorModeLabel(mode: string | null | undefined): string {
  if (mode === 'mono') return 'P&B'
  if (mode === 'color') return 'Color'
  return '—'
}

export function ColorModeCorrectionModal({
  job,
  open,
  onClose,
}: ColorModeCorrectionModalProps) {
  const queryClient = useQueryClient()
  const filters = job ? jobToLineFilters(job) : null
  const [confirmOverride, setConfirmOverride] = useState<{
    lineId: number
    mode: 'mono' | 'color'
  } | null>(null)

  const linesQuery = useQuery({
    queryKey: ['job-lines', filters],
    queryFn: () => fetchJobLines(filters!),
    enabled: open && filters != null,
  })

  const patch = useMutation({
    mutationFn: ({ lineId, mode }: { lineId: number; mode: 'mono' | 'color' }) =>
      patchLineColorMode(lineId, mode),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['job-lines', filters] })
      void queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })

  const allLines = linesQuery.data ?? []
  const pendingLines = allLines.filter(isPendingLine)
  const classifiedLines = allLines.filter((line) => !isPendingLine(line))

  async function applyBulk(mode: 'mono' | 'color') {
    await Promise.all(
      pendingLines.map((line) => patch.mutateAsync({ lineId: line.id, mode })),
    )
  }

  async function handleConfirmOverride() {
    if (!confirmOverride) return
    try {
      await patch.mutateAsync(confirmOverride)
      setConfirmOverride(null)
    } catch {
      // ErrorBanner handled by mutation state if needed
    }
  }

  function renderLineActions(line: JobLineOut) {
    const source = line.color_mode_source
    const pending = isPendingLine(line)

    if (source === 'manual') {
      return (
        <span className="text-xs text-[var(--text-secondary)]">
          {colorModeLabel(line.color_mode)}
        </span>
      )
    }

    if (pending) {
      return (
        <div className="flex gap-2">
          <Button
            variant="secondary"
            className="min-h-8 px-2 text-xs"
            disabled={patch.isPending}
            onClick={() => void patch.mutateAsync({ lineId: line.id, mode: 'mono' })}
          >
            P&B
          </Button>
          <Button
            variant="primary"
            className="min-h-8 px-2 text-xs"
            disabled={patch.isPending}
            onClick={() => void patch.mutateAsync({ lineId: line.id, mode: 'color' })}
          >
            Color
          </Button>
        </div>
      )
    }

    return (
      <div className="flex gap-2">
        <Button
          variant="secondary"
          className="min-h-8 px-2 text-xs"
          disabled={patch.isPending}
          onClick={() => setConfirmOverride({ lineId: line.id, mode: 'mono' })}
        >
          P&B
        </Button>
        <Button
          variant="primary"
          className="min-h-8 px-2 text-xs"
          disabled={patch.isPending}
          onClick={() => setConfirmOverride({ lineId: line.id, mode: 'color' })}
        >
          Color
        </Button>
      </div>
    )
  }

  return (
    <>
      <Dialog
        open={open}
        onClose={onClose}
        title="Corrigir modo de cor"
        footer={<Button variant="ghost" onClick={onClose}>Fechar</Button>}
      >
        {!job || !filters ? (
          <p className="text-sm text-[var(--text-secondary)]">
            Grupo sem chave de agregação — não é possível carregar linhas.
          </p>
        ) : linesQuery.isError ? (
          <ErrorBanner
            message="Erro ao carregar linhas do job."
            onRetry={() => void linesQuery.refetch()}
          />
        ) : linesQuery.isLoading ? (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : allLines.length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">
            Nenhuma linha encontrada neste grupo.
          </p>
        ) : (
          <>
            {pendingLines.length > 0 ? (
              <div className="mb-3 flex flex-wrap gap-2">
                <Button
                  variant="secondary"
                  className="min-h-8 text-xs"
                  disabled={patch.isPending}
                  onClick={() => void applyBulk('mono')}
                >
                  Aplicar P&B a todas pendentes
                </Button>
                <Button
                  variant="primary"
                  className="min-h-8 text-xs"
                  disabled={patch.isPending}
                  onClick={() => void applyBulk('color')}
                >
                  Aplicar Color a todas pendentes
                </Button>
              </div>
            ) : null}
            <ul className="flex max-h-[360px] flex-col gap-2 overflow-auto">
              {allLines.map((line) => (
                <li
                  key={line.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--border-subtle)] px-3 py-2 text-sm"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[var(--text-secondary)]">
                      {formatDateTime(line.timestamp)}
                    </span>
                    <Badge variant={sourceBadgeVariant(line.color_mode_source)}>
                      {sourceLabel(line.color_mode_source)}
                    </Badge>
                    {!isPendingLine(line) ? (
                      <span className="text-xs text-[var(--text-tertiary)]">
                        {colorModeLabel(line.color_mode)}
                      </span>
                    ) : null}
                  </div>
                  {renderLineActions(line)}
                </li>
              ))}
            </ul>
            {classifiedLines.length > 0 && pendingLines.length === 0 ? (
              <p className="mt-3 text-xs text-[var(--text-tertiary)]">
                Todas as linhas já classificadas. Use os botões para substituir por correção manual.
              </p>
            ) : null}
          </>
        )}
      </Dialog>

      <ConfirmDialog
        open={confirmOverride != null}
        title="Substituir classificação"
        message="Este valor veio do CUPS/sistema. Substituir por correção manual?"
        confirmLabel="Substituir"
        loading={patch.isPending}
        onConfirm={() => void handleConfirmOverride()}
        onClose={() => setConfirmOverride(null)}
      />
    </>
  )
}
