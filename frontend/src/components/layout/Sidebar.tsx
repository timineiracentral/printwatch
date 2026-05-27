import { Briefcase, Menu, X } from 'lucide-react'

export interface SidebarProps {
  mobileOpen: boolean
  onMobileToggle: () => void
}

export function Sidebar({ mobileOpen, onMobileToggle }: SidebarProps) {
  return (
    <>
      <button
        type="button"
        className="fixed left-4 top-4 z-50 inline-flex size-11 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-primary)] lg:hidden focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]"
        aria-expanded={mobileOpen}
        aria-controls="app-sidebar"
        aria-label={mobileOpen ? 'Fechar menu' : 'Abrir menu'}
        onClick={onMobileToggle}
      >
        {mobileOpen ? <X className="size-5" aria-hidden /> : <Menu className="size-5" aria-hidden />}
      </button>

      {mobileOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/20 lg:hidden"
          aria-label="Fechar menu"
          onClick={onMobileToggle}
        />
      ) : null}

      <aside
        id="app-sidebar"
        className={[
          'fixed inset-y-0 left-0 z-40 flex w-[220px] flex-col border-r border-[var(--border-subtle)] bg-[var(--bg-surface)] px-4 py-6 transition-transform duration-200 lg:static lg:translate-x-0',
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        ].join(' ')}
      >
        <div className="mb-8 px-2">
          <span className="text-[17px] font-semibold text-[var(--text-primary)]">PrintWatch</span>
        </div>
        <nav aria-label="Principal">
          <a
            href="#"
            aria-current="page"
            className="flex items-center gap-2 rounded-lg bg-[var(--accent-tint)] px-3 py-2 text-sm font-semibold text-[var(--accent)]"
          >
            <Briefcase className="size-4" aria-hidden />
            Jobs
          </a>
        </nav>
      </aside>
    </>
  )
}
