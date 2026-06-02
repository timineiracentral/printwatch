import { AppShell } from '../components/layout/AppShell'
import { PageHeader } from '../components/layout/PageHeader'
import { ManagerFilterBar } from '../components/manager/ManagerFilterBar'
import { ManagerKpiCards } from '../components/manager/ManagerKpiCards'
import { ManagerTopTables } from '../components/manager/ManagerTopTables'
import { FleetSummarySection } from '../components/manager/FleetSummarySection'
import { MeterReconciliationTable } from '../components/manager/MeterReconciliationTable'
import { PendingPagesBanner } from '../components/manager/PendingPagesBanner'
import { useManagerSummary } from '../hooks/useManagerSummary'
import { useUrlManagerFilters } from '../hooks/useUrlManagerFilters'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { Skeleton } from '../components/ui/Skeleton'

export function ManagerPage() {
  const { filters, applyDatePreset, setFilters } = useUrlManagerFilters()
  const { data, isLoading, isError, refetch } = useManagerSummary(
    filters.date_from,
    filters.date_to,
    filters.preset,
  )

  return (
    <AppShell
      header={<PageHeader title="Painel gerencial" />}
    >
      <div className="flex min-h-0 flex-1 flex-col gap-6">
        <ManagerFilterBar
          filters={filters}
          onPreset={applyDatePreset}
          onCustomDates={(date_from, date_to) =>
            setFilters({ date_from, date_to, preset: 'custom' })
          }
        />

        {data?.pending_pct != null && data.pending_count > 0 ? (
          <PendingPagesBanner
            pendingPct={data.pending_pct}
            pendingCount={data.pending_count}
          />
        ) : null}

        <ManagerKpiCards filters={filters} />

        {isError ? (
          <ErrorBanner
            message="Erro ao carregar rankings e reconciliação."
            onRetry={() => {
              void refetch()
            }}
          />
        ) : isLoading && !data ? (
          <Skeleton className="h-64 rounded-xl" />
        ) : data ? (
          <>
            <ManagerTopTables
              topUsers={data.top_users}
              topPrinters={data.top_printers}
              topDepartments={data.top_departments}
              hasRates={data.has_rates}
            />
            {data.fleet_summary ? (
              <FleetSummarySection fleetSummary={data.fleet_summary} />
            ) : null}
            <MeterReconciliationTable
              rows={data.meter_reconciliation}
              hasRates={data.has_rates}
            />
          </>
        ) : null}
      </div>
    </AppShell>
  )
}
