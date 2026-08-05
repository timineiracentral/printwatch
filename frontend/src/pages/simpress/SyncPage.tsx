import { RefreshCw } from 'lucide-react'
import { useState } from 'react'
import { ApiError } from '../../api/client'
import { PageHeader } from '../../components/layout/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import { Skeleton } from '../../components/ui/Skeleton'
import { useSimpressSync } from '../../hooks/useSimpressSync'
import { formatDateTime } from '../../lib/format'

const MAX_ERRORS_VISIBLE = 5

function truncateError(msg: string, max = 120): string {
  return msg.length <= max ? msg : `${msg.slice(0, max - 1)}…`
}

function isNeverRunError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404
}

export function SyncPage() {
  const { status, last, trigger } = useSimpressSync()
  const [flash, setFlash] = useState<string | null>(null)
  const [triggerError, setTriggerError] = useState<string | null>(null)

  const inProgress = status.data?.in_progress ?? false
  const summary = last.data
  const neverRun = last.isError && isNeverRunError(last.error)
  const loadError = last.isError && !neverRun

  async function handleSync() {
    setTriggerError(null)
    setFlash(null)
    try {
      await trigger.mutateAsync()
      setFlash('Sincronização iniciada.')
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setTriggerError('Já existe uma sincronização em andamento.')
      } else {
        setTriggerError('Não foi possível iniciar a sincronização. Tente novamente.')
      }
    }
  }

  const visibleErrors = summary?.errors.slice(0, MAX_ERRORS_VISIBLE) ?? []
  const hiddenErrors = (summary?.errors.length ?? 0) - visibleErrors.length

  return (
    <>
      <PageHeader
        title="Sync"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {inProgress ? (
              <span
                className="flex items-center gap-2 text-sm text-[var(--text-secondary)]"
                aria-live="polite"
              >
                <RefreshCw
                  className="size-4 animate-spin motion-reduce:animate-none"
                  aria-hidden
                />
                Sync em andamento…
              </span>
            ) : null}
            <Button
              variant="primary"
              className={inProgress ? 'min-h-11 opacity-50' : 'min-h-11'}
              disabled={inProgress || trigger.isPending}
              onClick={() => void handleSync()}
            >
              Sincronizar agora
            </Button>
          </div>
        }
      />

      {flash ? (
        <div className="mb-4 rounded-lg border border-[var(--accent)] bg-[var(--accent-tint)] px-4 py-2 text-sm text-[var(--accent)]">
          {flash}
        </div>
      ) : null}
      {triggerError ? (
        <div className="mb-4">
          <ErrorBanner message={triggerError} />
        </div>
      ) : null}

      <p className="mb-6 text-xs text-[var(--text-secondary)]">
        Sync automático diário às 08:00 (horário de Brasília).
      </p>

      <section
        className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4"
        aria-labelledby="sync-last-title"
      >
        <h2 id="sync-last-title" className="mb-4 text-[17px] font-semibold text-[var(--text-primary)]">
          Última sincronização
        </h2>

        {last.isLoading ? (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 4 }, (_, i) => (
              <Skeleton key={i} className="h-4 w-full max-w-xs" />
            ))}
          </div>
        ) : loadError ? (
          <ErrorBanner
            message="Erro ao carregar diagnóstico de sync."
            onRetry={() => void last.refetch()}
          />
        ) : neverRun || summary == null ? (
          <p className="text-center text-sm text-[var(--text-secondary)]">
            Nenhuma sincronização registrada ainda. Dispare a primeira com{' '}
            <strong>Sincronizar agora</strong>.
          </p>
        ) : (
          <>
            <div className="mb-4 flex flex-wrap items-center gap-2">
              {summary.ok ? (
                <Badge>Concluída com sucesso</Badge>
              ) : (
                <Badge variant="warning">Concluída com erros</Badge>
              )}
              {summary.finished_at ? (
                <span className="text-sm text-[var(--text-secondary)]">
                  Concluída em {formatDateTime(summary.finished_at)}
                </span>
              ) : null}
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-xs font-medium uppercase text-[var(--text-secondary)]">
                  Contratos
                </p>
                <p className="text-sm text-[var(--text-primary)]">
                  Contratos consultados: {summary.contracts_count}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase text-[var(--text-secondary)]">
                  Faturas
                </p>
                <p className="text-sm text-[var(--text-primary)]">
                  Faturas atualizadas: {summary.invoices_upserted}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase text-[var(--text-secondary)]">
                  Boletos
                </p>
                <p className="text-sm text-[var(--text-primary)]">
                  Boletos baixados: {summary.zips_downloaded}
                </p>
              </div>
            </div>
            {summary.cnpj_warnings.length > 0 ? (
              <div className="mt-4">
                <h3 className="mb-2 text-xs font-medium uppercase text-[var(--text-secondary)]">
                  CNPJs sem fatura
                </h3>
                <ul className="space-y-1">
                  {summary.cnpj_warnings.map((cnpj) => (
                    <li key={cnpj} className="font-mono text-xs text-[var(--text-primary)]">
                      {cnpj}
                      <span className="ml-2 font-sans text-[var(--text-secondary)]">
                        Nenhuma fatura encontrada no portal para este CNPJ.
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <div className="mt-4">
              <h3 className="mb-2 text-xs font-medium uppercase text-[var(--text-secondary)]">
                Erros
              </h3>
              {summary.errors.length === 0 ? (
                <p className="text-sm text-[var(--text-secondary)]">Nenhum erro registrado.</p>
              ) : (
                <ul
                  role="alert"
                  className="list-inside list-disc space-y-1 text-sm text-[var(--destructive)]"
                >
                  {visibleErrors.map((e, i) => (
                    <li key={i}>{truncateError(e)}</li>
                  ))}
                </ul>
              )}
              {hiddenErrors > 0 ? (
                <p className="mt-2 text-xs text-[var(--text-tertiary)]">
                  + {hiddenErrors} erros
                </p>
              ) : null}
            </div>
          </>
        )}
      </section>
    </>
  )
}
