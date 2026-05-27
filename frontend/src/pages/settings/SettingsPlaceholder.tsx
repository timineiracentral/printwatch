import { PageHeader } from '../../components/layout/PageHeader'

export function SettingsPlaceholder({ title }: { title: string }) {
  return (
    <>
      <PageHeader title={title} />
      <p className="text-sm text-[var(--text-secondary)]">Carregando…</p>
    </>
  )
}
