import { format, parseISO } from 'date-fns'
import { FileText } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../components/layout/PageHeader'
import { SettingsSearch } from '../../components/settings/SettingsSearch'
import { Badge } from '../../components/ui/Badge'
import { EmptyState } from '../../components/ui/EmptyState'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import { Skeleton } from '../../components/ui/Skeleton'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { useSimpressInvoices } from '../../hooks/useSimpressInvoices'
import { formatBrl } from '../../lib/format'

function formatDueDate(iso: string | null): string {
  if (!iso) return '—'
  return format(parseISO(iso), 'dd/MM/yyyy')
}

export function FaturasPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const { data, isLoading, isError, refetch } = useSimpressInvoices(
    debouncedSearch.trim() || undefined,
  )

  const items = data ?? []

  return (
    <>
      <PageHeader title="Faturas" />
      <SettingsSearch value={search} onChange={setSearch} placeholder="Buscar por CNPJ ou nota" />

      {isError ? (
        <ErrorBanner message="Erro ao carregar faturas." onRetry={() => void refetch()} />
      ) : isLoading ? (
        <div className="mt-4 overflow-hidden rounded-xl border border-[var(--border-subtle)]">
          <table className="w-full text-sm">
            <tbody>
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td colSpan={6} className="px-3 py-3">
                    <Skeleton className="h-4 w-full" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4 overflow-x-auto rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-subtle)] text-left text-xs font-medium uppercase text-[var(--text-tertiary)]">
                <th className="px-3 py-2">CNPJ</th>
                <th className="px-3 py-2">Nota</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Valor</th>
                <th className="px-3 py-2">Vencimento</th>
                <th className="px-3 py-2">Boleto (ZIP)</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={6}>
                    <EmptyState
                      icon={<FileText className="mx-auto size-10" />}
                      heading="Nenhuma fatura em aberto"
                      body="Quando o sync encontrar faturas vencidas ou a vencer, elas aparecerão aqui."
                      actionLabel="Ir para Sync"
                      onAction={() => navigate('/simpress/sync')}
                    />
                  </td>
                </tr>
              ) : (
                items.map((inv, idx) => (
                  <tr key={inv.id} className={idx % 2 === 1 ? 'bg-[var(--bg-muted)]/40' : ''}>
                    <td className="px-3 py-2 font-mono text-xs">{inv.cnpj}</td>
                    <td className="px-3 py-2 font-mono text-xs">{inv.invoice_number}</td>
                    <td className="px-3 py-2">
                      {inv.status === 'Vencido' ? (
                        <Badge variant="warning">Vencido</Badge>
                      ) : (
                        <Badge>A vencer</Badge>
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {formatBrl(Number(inv.amount))}
                    </td>
                    <td className="px-3 py-2">{formatDueDate(inv.due_at)}</td>
                    <td className="px-3 py-2">
                      {inv.has_zip ? (
                        <Badge>Sim</Badge>
                      ) : (
                        <span className="text-[var(--text-tertiary)]">Não</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
