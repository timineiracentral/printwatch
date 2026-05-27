import { Coins } from 'lucide-react'
import { useState } from 'react'
import { PageHeader } from '../../components/layout/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { EmptyState } from '../../components/ui/EmptyState'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import { Input } from '../../components/ui/Input'
import { Skeleton } from '../../components/ui/Skeleton'
import { useCostRates } from '../../hooks/useCostRates'
import { formatBrl, formatDateTime } from '../../lib/format'
import type { CostRateCreate } from '../../types/api'

function parseRateInput(value: string): number | null {
  const normalized = value.trim().replace(',', '.')
  if (!normalized) return null
  const n = Number(normalized)
  return Number.isFinite(n) && n >= 0 ? n : null
}

function formatRateDisplay(rate: string): string {
  const n = Number(rate)
  return Number.isFinite(n) ? formatBrl(n) : rate
}

export function CostRatesPage() {
  const { list, current, create } = useCostRates()
  const [rateMono, setRateMono] = useState('')
  const [rateColor, setRateColor] = useState('')
  const [validFrom, setValidFrom] = useState('')
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    const mono = parseRateInput(rateMono)
    const color = parseRateInput(rateColor)
    if (mono === null || color === null) {
      setFormError('Informe tarifas mono e color válidas (≥ 0).')
      return
    }
    const payload: CostRateCreate = {
      rate_mono: mono,
      rate_color: color,
    }
    if (validFrom.trim()) {
      payload.valid_from = `${validFrom.trim()}T00:00:00`
    }
    try {
      await create.mutateAsync(payload)
      setRateMono('')
      setRateColor('')
      setValidFrom('')
      setSuccessMsg('Nova vigência cadastrada.')
    } catch {
      setFormError('Não foi possível salvar a tarifa.')
    }
  }

  return (
    <>
      <PageHeader title="Tarifas" />
      {successMsg ? (
        <div className="mb-4 rounded-lg border border-[var(--accent)] bg-[var(--accent-tint)] px-4 py-2 text-sm text-[var(--accent)]">
          {successMsg}
        </div>
      ) : null}

      <section className="mb-8 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
        <h2 className="mb-3 text-sm font-semibold text-[var(--text-primary)]">Tarifa vigente</h2>
        {current.isLoading ? (
          <Skeleton className="h-6 w-48" />
        ) : current.isError ? (
          <p className="text-sm text-[var(--text-secondary)]">Nenhuma tarifa configurada.</p>
        ) : current.data ? (
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-[var(--text-secondary)]">Mono</dt>
              <dd className="font-medium tabular-nums">{formatRateDisplay(current.data.rate_mono)}</dd>
            </div>
            <div>
              <dt className="text-[var(--text-secondary)]">Color</dt>
              <dd className="font-medium tabular-nums">{formatRateDisplay(current.data.rate_color)}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-[var(--text-secondary)]">Vigente desde</dt>
              <dd>{formatDateTime(current.data.valid_from)}</dd>
            </div>
          </dl>
        ) : null}
      </section>

      <section className="mb-8 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
        <h2 className="mb-3 text-sm font-semibold text-[var(--text-primary)]">Nova vigência</h2>
        <form onSubmit={(e) => void handleSubmit(e)} className="flex max-w-md flex-col gap-3">
          {formError ? <ErrorBanner message={formError} /> : null}
          <Input
            label="Tarifa mono (R$)"
            required
            inputMode="decimal"
            value={rateMono}
            onChange={(e) => setRateMono(e.target.value)}
          />
          <Input
            label="Tarifa color (R$)"
            required
            inputMode="decimal"
            value={rateColor}
            onChange={(e) => setRateColor(e.target.value)}
          />
          <Input
            label="Vigente a partir de (opcional)"
            type="date"
            value={validFrom}
            onChange={(e) => setValidFrom(e.target.value)}
          />
          <Button variant="primary" type="submit" disabled={create.isPending}>
            Cadastrar vigência
          </Button>
        </form>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-[var(--text-primary)]">Histórico</h2>
        {list.isError ? (
          <ErrorBanner message="Erro ao carregar histórico." onRetry={() => void list.refetch()} />
        ) : (
          <div className="overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border-subtle)]">
                  {['Vigência desde', 'Mono', 'Color', 'Cadastro'].map((h) => (
                    <th
                      key={h}
                      scope="col"
                      className="px-3 py-2 text-left text-xs font-medium uppercase text-[var(--text-secondary)]"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {list.isLoading
                  ? Array.from({ length: 3 }, (_, i) => (
                      <tr key={i}>
                        {Array.from({ length: 4 }, (_, j) => (
                          <td key={j} className="px-3 py-2">
                            <Skeleton className="h-4 w-24" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : (list.data ?? []).length === 0
                    ? (
                        <tr>
                          <td colSpan={4}>
                            <EmptyState
                              icon={<Coins className="mx-auto size-10" />}
                              heading="Nenhuma tarifa cadastrada"
                            />
                          </td>
                        </tr>
                      )
                    : (list.data ?? []).map((row, idx) => {
                        const isCurrent = current.data?.id === row.id
                        return (
                          <tr
                            key={row.id}
                            className={idx % 2 === 1 ? 'bg-[var(--bg-muted)]/40' : ''}
                          >
                            <td className="px-3 py-2 whitespace-nowrap">
                              {formatDateTime(row.valid_from)}
                              {isCurrent ? (
                                <Badge className="ml-2">Vigente</Badge>
                              ) : null}
                            </td>
                            <td className="px-3 py-2 tabular-nums">{formatRateDisplay(row.rate_mono)}</td>
                            <td className="px-3 py-2 tabular-nums">{formatRateDisplay(row.rate_color)}</td>
                            <td className="px-3 py-2 text-[var(--text-secondary)]">
                              {formatDateTime(row.created_at)}
                            </td>
                          </tr>
                        )
                      })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}
