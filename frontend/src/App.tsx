import { AppShell } from './components/layout/AppShell'
import { PageHeader } from './components/layout/PageHeader'
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
      <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-6 text-sm text-[var(--text-secondary)]">
        Cards, filtros e tabela serão adicionados nos próximos passos.
      </div>
    </AppShell>
  )
}
