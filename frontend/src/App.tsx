import { AppShell } from './components/layout/AppShell'
import { PageHeader } from './components/layout/PageHeader'
import { SummaryCards } from './components/summary/SummaryCards'
import { Button } from './components/ui/Button'

export default function App() {
  return (
    <AppShell
      header={
        <PageHeader
          title="Histórico de impressão"
          actions={
            <Button variant="secondary" disabled>
              Exportar CSV
            </Button>
          }
        />
      }
    >
      <div className="flex flex-col gap-6">
        <SummaryCards />
        <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-6 text-sm text-[var(--text-secondary)]">
          Filtros e tabela serão adicionados no próximo passo.
        </div>
      </div>
    </AppShell>
  )
}
