import { Link } from 'react-router-dom'
import { Badge } from '../ui/Badge'
import { TonerBar } from '../fleet/TonerBar'
import type { FleetSummaryBlock } from '../../types/api'

export interface FleetSummarySectionProps {
  fleetSummary: FleetSummaryBlock
}

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

export function FleetSummarySection({ fleetSummary }: FleetSummarySectionProps) {
  const { counts, items } = fleetSummary

  return (
    <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-[var(--text-primary)]">Frota</h2>
        <Link
          to="/fleet"
          className="text-sm font-medium text-[var(--accent)] hover:underline"
        >
          Ver frota completa
        </Link>
      </div>

      <p className="mb-3 text-sm text-[var(--text-secondary)]">
        {counts.online} online · {counts.offline} offline · {counts.unknown} desconhecido
      </p>

      {items.length === 0 ? (
        <p className="text-sm text-[var(--text-tertiary)]">Nenhuma impressora ativa.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[480px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-[var(--border-subtle)] text-left text-xs text-[var(--text-secondary)]">
                <th className="py-2 pr-3 font-medium">Impressora</th>
                <th className="py-2 pr-3 font-medium">Status</th>
                <th className="py-2 font-medium">Toner</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.printer_id} className="border-b border-[var(--border-subtle)]">
                  <td className="py-2 pr-3">{row.display_name}</td>
                  <td className="py-2 pr-3">
                    <Badge variant={statusBadgeVariant(row.fleet_status)}>
                      {statusLabel(row.fleet_status)}
                    </Badge>
                  </td>
                  <td className="py-2">
                    <TonerBar
                      snmpEnabled={row.snmp_enabled}
                      toner={
                        row.toner_status
                          ? {
                              status: row.toner_status as 'ok' | 'unavailable',
                              black_pct: row.black_pct,
                              color_pct: null,
                              partial_color: false,
                            }
                          : null
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
