import { AppShell } from '../components/layout/AppShell'
import { PageHeader } from '../components/layout/PageHeader'
import { FilterBar } from '../components/filters/FilterBar'
import { JobsPagination } from '../components/jobs/JobsPagination'
import { JobsTable } from '../components/jobs/JobsTable'
import { ExportCsvButton } from '../components/export/ExportCsvButton'
import { SummaryCards } from '../components/summary/SummaryCards'

export function JobsPage() {
  return (
    <AppShell
      header={
        <PageHeader
          title="Histórico de impressão"
          actions={<ExportCsvButton />}
        />
      }
    >
      <div className="flex min-h-0 flex-1 flex-col gap-6">
        <SummaryCards />
        <FilterBar />
        <section className="flex min-h-[480px] flex-1 flex-col gap-3">
          <JobsTable />
          <JobsPagination />
        </section>
      </div>
    </AppShell>
  )
}
