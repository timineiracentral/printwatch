import type { ManagerTopEntry } from '../../types/api'
import { formatBrl, formatNumberPtBr } from '../../lib/format'

export interface ManagerTopTablesProps {
  topUsers: ManagerTopEntry[]
  topPrinters: ManagerTopEntry[]
  topDepartments: ManagerTopEntry[]
  hasRates: boolean
}

function TopTable({
  title,
  rows,
  hasRates,
}: {
  title: string
  rows: ManagerTopEntry[]
  hasRates: boolean
}) {
  return (
    <section className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-4">
      <h3 className="mb-3 text-sm font-semibold text-[var(--text-primary)]">{title}</h3>
      {rows.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]">Sem dados no período</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-[var(--text-tertiary)]">
              <th className="pb-2 font-medium">Nome</th>
              <th className="pb-2 text-right font-medium">Páginas</th>
              {hasRates ? (
                <th className="pb-2 text-right font-medium">Custo</th>
              ) : null}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.name} className="border-t border-[var(--border-subtle)]">
                <td className="py-2 pr-2 text-[var(--text-primary)]">{row.name}</td>
                <td className="py-2 text-right tabular-nums">
                  {formatNumberPtBr(row.pages)}
                </td>
                {hasRates ? (
                  <td className="py-2 text-right tabular-nums text-[var(--text-secondary)]">
                    {row.estimated_cost != null
                      ? formatBrl(Number(row.estimated_cost))
                      : '—'}
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

export function ManagerTopTables({
  topUsers,
  topPrinters,
  topDepartments,
  hasRates,
}: ManagerTopTablesProps) {
  return (
    <div className="flex flex-col gap-4">
      <TopTable title="Top 10 usuários" rows={topUsers} hasRates={hasRates} />
      <TopTable title="Top 10 impressoras" rows={topPrinters} hasRates={hasRates} />
      <TopTable
        title="Top 10 departamentos"
        rows={topDepartments}
        hasRates={hasRates}
      />
    </div>
  )
}
