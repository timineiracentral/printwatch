import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchJobLines, patchLineColorMode } from '../../api/jobs'
import { formatDateTime } from '../../lib/format'
import type { JobLineFilters, JobOut } from '../../types/api'
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

export function ColorModeCorrectionModal({
  job,
  open,
  onClose,
}: ColorModeCorrectionModalProps) {
  const queryClient = useQueryClient()
  const filters = job ? jobToLineFilters(job) : null

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

  const pendingLines =
    linesQuery.data?.filter((line) => line.color_mode == null) ?? []

  return (
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
      ) : pendingLines.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]">
          Nenhuma linha pendente de classificação neste grupo.
        </p>
      ) : (
        <ul className="flex max-h-[360px] flex-col gap-2 overflow-auto">
          {pendingLines.map((line) => (
            <li
              key={line.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--border-subtle)] px-3 py-2 text-sm"
            >
              <span className="text-[var(--text-secondary)]">
                {formatDateTime(line.timestamp)}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  className="min-h-8 px-2 text-xs"
                  disabled={patch.isPending}
                  onClick={() =>
                    void patch.mutateAsync({ lineId: line.id, mode: 'mono' })
                  }
                >
                  P&B
                </Button>
                <Button
                  variant="primary"
                  className="min-h-8 px-2 text-xs"
                  disabled={patch.isPending}
                  onClick={() =>
                    void patch.mutateAsync({ lineId: line.id, mode: 'color' })
                  }
                >
                  Color
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {linesQuery.data && linesQuery.data.length > pendingLines.length ? (
        <p className="mt-3 text-xs text-[var(--text-tertiary)]">
          <Badge variant="muted">Dica</Badge>{' '}
          Linhas já classificadas não aparecem aqui.
        </p>
      ) : null}
    </Dialog>
  )
}
