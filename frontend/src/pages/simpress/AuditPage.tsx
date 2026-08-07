import { format, parseISO } from 'date-fns'
import { ScrollText } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../components/layout/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { EmptyState } from '../../components/ui/EmptyState'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import { Skeleton } from '../../components/ui/Skeleton'
import { useSimpressAudit } from '../../hooks/useSimpressAudit'
import type { MessageAuditRead } from '../../types/api'

const STAGE_LABELS: Record<string, string> = {
  new: 'Lançamento',
  reminded_5d: '+5 dias',
  reminded_10d: '+10 dias',
  overdue_urgent: 'Urgente',
}

const PART_LABELS: Record<string, string> = {
  text: 'Texto',
  document: 'Documento',
}

function formatTimestamp(iso: string): string {
  return format(parseISO(iso), 'dd/MM/yyyy HH:mm')
}

function stageLabel(stage: string): string {
  return STAGE_LABELS[stage] ?? stage
}

function partLabel(part: string): string {
  return PART_LABELS[part] ?? part
}

function contactDisplay(row: MessageAuditRead): { text: string; mono: boolean } {
  if (row.contact_name?.trim()) return { text: row.contact_name.trim(), mono: false }
  if (row.contact_phone?.trim()) return { text: row.contact_phone.trim(), mono: true }
  return { text: '—', mono: false }
}

function truncateMid(value: string, max = 24): { display: string; title?: string } {
  if (value.length <= max) return { display: value }
  const half = Math.floor((max - 1) / 2)
  return {
    display: `${value.slice(0, half)}…${value.slice(-half)}`,
    title: value,
  }
}

function variantDisplay(row: MessageAuditRead): string {
  if (row.part === 'document' || !row.variant_id) return '—'
  return row.variant_id
}

function providerDisplay(row: MessageAuditRead): { display: string; title?: string } {
  if (!row.provider_message_id) return { display: '—' }
  return truncateMid(row.provider_message_id)
}

export function AuditPage() {
  const navigate = useNavigate()
  const { data, isLoading, isError, refetch } = useSimpressAudit(100)

  const items = data ?? []

  return (
    <>
      <PageHeader title="Audit" />
      <p className="text-xs text-[var(--text-secondary)]">
        Tentativas de envio WhatsApp (resumo). Mais recentes primeiro.
      </p>

      {isError ? (
        <ErrorBanner message="Erro ao carregar audit." onRetry={() => void refetch()} />
      ) : isLoading ? (
        <div className="mt-4 overflow-hidden rounded-xl border border-[var(--border-subtle)]">
          <table className="w-full text-sm">
            <tbody>
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td colSpan={8} className="px-3 py-3">
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
                <th scope="col" className="px-3 py-2">
                  Quando
                </th>
                <th scope="col" className="px-3 py-2">
                  Resultado
                </th>
                <th scope="col" className="px-3 py-2">
                  Estágio
                </th>
                <th scope="col" className="px-3 py-2">
                  Tipo
                </th>
                <th scope="col" className="px-3 py-2">
                  Contato
                </th>
                <th scope="col" className="px-3 py-2">
                  HTTP
                </th>
                <th scope="col" className="px-3 py-2">
                  Variant
                </th>
                <th scope="col" className="px-3 py-2">
                  Provider
                </th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={8}>
                    <EmptyState
                      icon={<ScrollText className="mx-auto size-10" />}
                      heading="Nenhum envio registrado"
                      body="Quando o pipeline de lembretes enviar mensagens, os registros aparecerão aqui."
                      actionLabel="Ir para Sync"
                      onAction={() => navigate('/simpress/sync')}
                    />
                  </td>
                </tr>
              ) : (
                items.map((row, idx) => {
                  const contact = contactDisplay(row)
                  const provider = providerDisplay(row)
                  const variant = variantDisplay(row)

                  return (
                    <tr key={row.id} className={idx % 2 === 1 ? 'bg-[var(--bg-muted)]/40' : ''}>
                      <td className="px-3 py-2">{formatTimestamp(row.created_at)}</td>
                      <td className="px-3 py-2">
                        {row.outcome === 'ok' ? (
                          <Badge>OK</Badge>
                        ) : (
                          <Badge variant="warning">Falha</Badge>
                        )}
                      </td>
                      <td className="px-3 py-2">{stageLabel(row.stage)}</td>
                      <td className="px-3 py-2">{partLabel(row.part)}</td>
                      <td
                        className={[
                          'px-3 py-2',
                          contact.mono ? 'font-mono text-xs' : '',
                        ].join(' ')}
                      >
                        {contact.text}
                      </td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {row.http_status ?? '—'}
                      </td>
                      <td className="px-3 py-2 font-mono text-xs">{variant}</td>
                      <td className="px-3 py-2 font-mono text-xs" title={provider.title}>
                        {provider.display}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
