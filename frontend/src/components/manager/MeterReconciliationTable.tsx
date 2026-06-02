import type { MeterReconciliationRow } from '../../types/api'
import { formatBrl, formatNumberPtBr } from '../../lib/format'

export interface MeterReconciliationTableProps {
  rows: MeterReconciliationRow[]
  hasRates: boolean
}

export function MeterReconciliationTable({
  rows,
  hasRates,
}: MeterReconciliationTableProps) {
  const withReadings = rows.filter(
    (r) => r.pages_meter != null || r.pages_jobs > 0,
  )

  return (
    <section className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-4">
      <h3 className="mb-3 text-sm font-semibold text-[var(--text-primary)]">
        Contador vs jobs
      </h3>
      {withReadings.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]">
          Nenhuma leitura de contador no período.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="text-left text-xs text-[var(--text-tertiary)]">
                <th className="pb-2 font-medium">Impressora</th>
                <th className="pb-2 text-right font-medium">Pág. contador</th>
                <th className="pb-2 text-right font-medium">Pág. jobs</th>
                <th className="pb-2 text-right font-medium">Divergência</th>
                {hasRates ? (
                  <th className="pb-2 text-right font-medium">Custo contador</th>
                ) : null}
                <th className="pb-2 font-medium">Obs.</th>
              </tr>
            </thead>
            <tbody>
              {withReadings.map((row) => (
                <tr
                  key={row.printer_id}
                  className="border-t border-[var(--border-subtle)]"
                >
                  <td className="py-2 pr-2">{row.printer_name}</td>
                  <td className="py-2 text-right tabular-nums">
                    {row.pages_meter != null
                      ? formatNumberPtBr(row.pages_meter)
                      : '—'}
                  </td>
                  <td className="py-2 text-right tabular-nums">
                    {formatNumberPtBr(row.pages_jobs)}
                  </td>
                  <td className="py-2 text-right tabular-nums">
                    {row.divergence_pct != null
                      ? `${row.divergence_pct.toFixed(1)}%`
                      : '—'}
                  </td>
                  {hasRates ? (
                    <td className="py-2 text-right tabular-nums">
                      {row.cost_meter != null
                        ? formatBrl(Number(row.cost_meter))
                        : '—'}
                    </td>
                  ) : null}
                  <td className="py-2 text-xs text-[var(--text-secondary)]">
                    {[
                      row.partial_interval ? 'intervalo parcial' : null,
                      row.counter_reset ? 'reset contador' : null,
                      row.proportional_cost_note,
                    ]
                      .filter(Boolean)
                      .join(' · ') || '—'}
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
