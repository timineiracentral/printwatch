import { Link } from 'react-router-dom'
import { Dialog } from '../ui/Dialog'
import { TonerBar } from './TonerBar'
import type { FleetPrinterRow } from '../../types/api'
import { formatDateTime } from '../../lib/format'

export interface FleetDetailDrawerProps {
  row: FleetPrinterRow | null
  open: boolean
  onClose: () => void
}

function statusLabel(status: string): string {
  if (status === 'online') return 'Online'
  if (status === 'offline') return 'Offline'
  return 'Desconhecido'
}

export function FleetDetailDrawer({ row, open, onClose }: FleetDetailDrawerProps) {
  if (!row) return null

  return (
    <Dialog open={open} onClose={onClose} title={row.display_name}>
      <div className="flex flex-col gap-4 text-sm">
        <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-2">
          <dt className="text-[var(--text-tertiary)]">Status</dt>
          <dd>{statusLabel(row.fleet_status)}</dd>
          <dt className="text-[var(--text-tertiary)]">Fonte</dt>
          <dd className="uppercase">{row.fleet_source}</dd>
          <dt className="text-[var(--text-tertiary)]">IP</dt>
          <dd>{row.ip_address ?? '—'}</dd>
          <dt className="text-[var(--text-tertiary)]">Última verificação</dt>
          <dd>
            {row.last_checked_at ? formatDateTime(row.last_checked_at) : '—'}
          </dd>
        </dl>

        <div>
          <p className="mb-2 text-xs font-medium uppercase text-[var(--text-tertiary)]">
            Toner
          </p>
          <TonerBar snmpEnabled={row.snmp_enabled} toner={row.toner} />
        </div>

        <Link
          to="/settings/printers"
          state={{ highlightPrinterId: row.printer_id }}
          onClick={onClose}
          className="inline-flex min-h-11 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--row-hover)]"
        >
          Editar cadastro
        </Link>
      </div>
    </Dialog>
  )
}
