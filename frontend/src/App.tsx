import { useUrlFilters } from './hooks/useUrlFilters'
import { useJobs } from './hooks/useJobs'
import { useStatsSummary } from './hooks/useStatsSummary'

export default function App() {
  const { filters } = useUrlFilters()
  const jobs = useJobs(filters)
  const stats = useStatsSummary()

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <pre className="text-sm text-[var(--text-secondary)]">
        {JSON.stringify(
          {
            jobsTotal: jobs.data?.total ?? null,
            hojeJobs: stats.data?.hoje.jobs ?? null,
          },
          null,
          2,
        )}
      </pre>
    </main>
  )
}
