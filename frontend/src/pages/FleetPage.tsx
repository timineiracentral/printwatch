import { useMemo, useState } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { PageHeader } from '../components/layout/PageHeader'
import { FleetDetailDrawer } from '../components/fleet/FleetDetailDrawer'
import { TonerBar } from '../components/fleet/TonerBar'
import { Badge } from '../components/ui/Badge'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { Skeleton } from '../components/ui/Skeleton'
import { useFleet } from '../hooks/useFleet'
import type { FleetPrinterRow } from '../types/api'
import { formatDateTime } from '../lib/format'

function statusBadgeVariant(status: string): 'default' | 'warning' | 'muted' {
  if (status === 'online') return 'default'
  if (status === 'offline') return 'warning'
  return 'muted'
}

function statusLabel(status: string): string {
  if (status === 'online') return 'Online'
  if (status === 'offline') return 'Offline'
  return 'Desconhecido'
}

export function FleetPage() {
  const { data, isLoading, isError, refetch } = useFleet()
  const [selected, setSelected] = useState<FleetPrinterRow | null>(null)

  const sorted = useMemo(() => {
    const items = [...(data?.items ?? [])]
    items.sort((a, b) => a.display_name.localeCompare(b.display_name, 'pt-BR'))
    return items
  }, [data?.items])

  const summary = data?.summary

  return (
    <AppShell header={<PageHeader title="Frota" />}>
      <div className="flex min-h-0 flex-1 flex-col gap-6">
        {isError ? (
          <ErrorBanner
            message="Erro ao carregar frota."
            onRetry={() => {
              void refetch()
            }}
          />
        ) : null}

        {isLoading && !data ? (
          <Skeleton className="h-24 rounded-xl" />
        ) : summary ? (
          <div className="grid gap-3 sm:grid-cols-4">
            {(
              [
                ['Online', summary.online],
                ['Offline', summary.offline],
                ['Desconhecido', summary.unknown],
                ['Total', summary.total],
              ] as const
            ).map(([label, count]) => (
              <div
                key={label}
                className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-4 py-3"
              >
                <p className="text-xs text-[var(--text-tertiary)]">{label}</p>
                <p className="text-2xl font-semibold tabular-nums text-[var(--text-primary)]">
                  {count}
                </p>
                <Badge variant="muted">{label}</Badge>
              </div>
            ))}
          </div>
        ) : null}

        <div className="overflow-auto rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <table className="w-full min-w-[720px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-[var(--border-subtle)] text-left text-xs text-[var(--text-secondary)]">
                <th className="px-3 py-2.5 font-medium">Nome</th>
                <th className="px-3 py-2.5 font-medium">Status</th>
                <th className="px-3 py-2.5 font-medium">IP</th>
                <th className="px-3 py-2.5 font-medium">Última verificação</th>
                <th className="px-3 py-2.5 font-medium">Toner</th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array.from({ length: 5 }, (_, i) => (
                    <tr key={i} className="border-b border-[var(--border-subtle)]">
                      <td colSpan={5} className="px-3 py-2">
                        <Skeleton className="h-8 w-full" />
                      </td>
                    </tr>
                  ))
                : sorted.map((row) => (
                    <tr
                      key={row.printer_id}
                      className="cursor-pointer border-b border-[var(--border-subtle)] hover:bg-[var(--row-hover)]"
                      onClick={() => setSelected(row)}
                    >
                      <td className="px-3 py-2 font-medium text-[var(--text-primary)]">
                        {row.display_name}
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant={statusBadgeVariant(row.fleet_status)}>
                          {statusLabel(row.fleet_status)}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-[var(--text-secondary)]">
                        {row.ip_address ?? '—'}
                      </td>
                      <td className="whitespace-nowrap px-3 py-2 text-[var(--text-secondary)]">
                        {row.last_checked_at
                          ? formatDateTime(row.last_checked_at)
                          : '—'}
                      </td>
                      <td className="px-3 py-2">
                        <TonerBar snmpEnabled={row.snmp_enabled} toner={row.toner} />
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      </div>

      <FleetDetailDrawer
        row={selected}
        open={selected != null}
        onClose={() => setSelected(null)}
      />
    </AppShell>
  )
}
