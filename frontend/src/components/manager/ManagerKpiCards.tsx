import { useManagerSummary } from '../../hooks/useManagerSummary'
import type { ManagerFilters } from '../../types/api'
import { ErrorBanner } from '../ui/ErrorBanner'
import { Skeleton } from '../ui/Skeleton'
import {
  ManagerKpiCard,
  formatCostValue,
  formatPagesSubtitle,
} from './ManagerKpiCard'
import { formatNumberPtBr } from '../../lib/format'

const ERROR_MESSAGE =
  'Não foi possível carregar o painel gerencial. Verifique o servidor e tente novamente.'

export interface ManagerKpiCardsProps {
  filters: ManagerFilters
}

export function ManagerKpiCards({ filters }: ManagerKpiCardsProps) {
  const { data, isLoading, isError, refetch } = useManagerSummary(
    filters.date_from,
    filters.date_to,
    filters.preset,
  )

  if (isLoading && !data) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-busy="true">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorBanner
        message={ERROR_MESSAGE}
        onRetry={() => {
          void refetch()
        }}
      />
    )
  }

  const period = data?.period
  const prev = period?.previous

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <ManagerKpiCard
        label="Páginas faturáveis"
        value={formatNumberPtBr(period?.pages_billable ?? 0)}
        subtitle={formatPagesSubtitle(
          period?.pages_mono ?? 0,
          period?.pages_color ?? 0,
        )}
        deltaPct={period?.delta_pct_pages}
        previousLabel={
          prev
            ? `Anterior: ${formatNumberPtBr(prev.pages_billable)} páginas`
            : undefined
        }
      />
      <ManagerKpiCard
        label="Custo estimado"
        value={formatCostValue(
          period?.estimated_cost != null
            ? Number(period.estimated_cost)
            : null,
          data?.has_rates ?? false,
        )}
        deltaPct={period?.delta_pct_cost}
        previousLabel={
          prev?.estimated_cost != null
            ? `Anterior: ${formatCostValue(Number(prev.estimated_cost), data?.has_rates ?? false)}`
            : undefined
        }
      />
      <ManagerKpiCard
        label="Páginas pendentes"
        value={formatNumberPtBr(period?.pages_pending ?? 0)}
        subtitle={
          data?.pending_pct != null
            ? `${data.pending_pct.toFixed(1)}% do volume`
            : undefined
        }
      />
      <ManagerKpiCard
        label="Tarifas no período"
        value={data?.has_rates ? 'Configuradas' : 'Sem tarifa'}
        subtitle={
          data?.has_rates ? undefined : 'Cadastre tarifas em Configurações'
        }
      />
    </div>
  )
}
