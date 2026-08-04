import {
  Activity,
  BarChart3,
  Briefcase,
  Building2,
  Coins,
  Contact,
  Menu,
  Printer,
  Upload,
  Users,
  Wallet,
  X,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useSimpressHealth } from '../../hooks/useSimpressHealth'

export interface SidebarProps {
  mobileOpen: boolean
  onMobileToggle: () => void
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors',
    isActive
      ? 'bg-[var(--accent-tint)] font-semibold text-[var(--accent)]'
      : 'text-[var(--text-secondary)] hover:bg-[var(--bg-muted)]',
  ].join(' ')

export function Sidebar({ mobileOpen, onMobileToggle }: SidebarProps) {
  const { data: simpressEnabled } = useSimpressHealth()

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
        <nav aria-label="Principal" className="flex flex-col gap-1">
          <NavLink to="/" end className={navLinkClass}>
            <Briefcase className="size-4" aria-hidden />
            Jobs
          </NavLink>
          <NavLink to="/manager" className={navLinkClass}>
            <BarChart3 className="size-4" aria-hidden />
            Gerencial
          </NavLink>
          <NavLink to="/fleet" className={navLinkClass}>
            <Activity className="size-4" aria-hidden />
            Frota
          </NavLink>

          {simpressEnabled ? (
            <>
              <p className="mb-2 mt-6 px-3 text-xs font-medium uppercase tracking-wide text-[var(--text-tertiary)]">
                Simpress
              </p>
              <NavLink to="/simpress/cnpjs" className={navLinkClass}>
                <Building2 className="size-4" aria-hidden />
                CNPJs
              </NavLink>
              <NavLink to="/simpress/contatos" className={navLinkClass}>
                <Contact className="size-4" aria-hidden />
                Contatos
              </NavLink>
            </>
          ) : null}

          <p className="mb-2 mt-6 px-3 text-xs font-medium uppercase tracking-wide text-[var(--text-tertiary)]">
            Configurações
          </p>
          <NavLink to="/settings/printers" className={navLinkClass}>
            <Printer className="size-4" aria-hidden />
            Impressoras
          </NavLink>
          <NavLink to="/settings/departments" className={navLinkClass}>
            <Building2 className="size-4" aria-hidden />
            Departamentos
          </NavLink>
          <NavLink to="/settings/cost-centers" className={navLinkClass}>
            <Wallet className="size-4" aria-hidden />
            Centros de custo
          </NavLink>
          <NavLink to="/settings/cost-rates" className={navLinkClass}>
            <Coins className="size-4" aria-hidden />
            Tarifas
          </NavLink>
          <NavLink to="/settings/users" className={navLinkClass}>
            <Users className="size-4" aria-hidden />
            Usuários
          </NavLink>
          <NavLink to="/settings/import" className={navLinkClass}>
            <Upload className="size-4" aria-hidden />
            Importar CSV
          </NavLink>
        </nav>
      </aside>
    </>
  )
}
