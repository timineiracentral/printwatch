import {
  Activity,
  BarChart3,
  Briefcase,
  Building2,
  Coins,
  Contact,
  FileText,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Printer,
  RefreshCw,
  ScrollText,
  Upload,
  Users,
  Wallet,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useSimpressHealth } from '../../hooks/useSimpressHealth'

export interface SidebarProps {
  mobileOpen: boolean
  onMobileToggle: () => void
}

const COLLAPSED_KEY = 'printwatch.sidebar-collapsed'

const navLinkClass =
  (collapsed: boolean) =>
  ({ isActive }: { isActive: boolean }) =>
    [
      'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors',
      collapsed ? 'lg:justify-center lg:px-2' : '',
      isActive
        ? 'bg-[var(--accent-tint)] font-semibold text-[var(--accent)]'
        : 'text-[var(--text-secondary)] hover:bg-[var(--bg-muted)]',
    ].join(' ')

export function Sidebar({ mobileOpen, onMobileToggle }: SidebarProps) {
  const { data: simpressEnabled } = useSimpressHealth()
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(COLLAPSED_KEY) === '1'
    } catch {
      return false
    }
  })

  const toggle = () => {
    setCollapsed(!collapsed)
    try {
      localStorage.setItem(COLLAPSED_KEY, collapsed ? '0' : '1')
    } catch {
      // ponytail: preferência não persiste se o storage estiver indisponível
    }
  }

  const label = collapsed ? 'lg:sr-only' : undefined
  const sectionClass = [
    'mb-2 mt-6 px-3 text-xs font-medium uppercase tracking-wide text-[var(--text-tertiary)]',
    collapsed ? 'lg:mx-2 lg:mb-2 lg:mt-4 lg:h-px lg:bg-[var(--border-subtle)] lg:p-0' : '',
  ].join(' ')
  const linkClass = navLinkClass(collapsed)
  const titleClass = 'text-[17px] font-semibold text-[var(--text-primary)]'

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
          'fixed inset-y-0 left-0 z-40 flex w-[220px] flex-col overflow-hidden border-r border-[var(--border-subtle)] bg-[var(--bg-surface)] px-4 py-6 transition-[transform,width] duration-200 motion-reduce:transition-none lg:static lg:translate-x-0',
          collapsed ? 'lg:w-16 lg:px-2' : '',
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        ].join(' ')}
      >
        <div
          className={[
            'mb-8 flex items-center justify-between gap-2 px-2',
            collapsed ? 'lg:flex-col lg:justify-center' : '',
          ].join(' ')}
        >
          <span className={[titleClass, collapsed ? 'lg:hidden' : ''].join(' ')}>PrintWatch</span>
          <span className={[titleClass, collapsed ? 'hidden lg:inline' : 'hidden'].join(' ')}>PW</span>
          <button
            type="button"
            className="hidden size-8 items-center justify-center rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-muted)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)] lg:inline-flex"
            aria-label={collapsed ? 'Expandir menu lateral' : 'Recolher menu lateral'}
            aria-expanded={!collapsed}
            aria-controls="app-sidebar"
            onClick={toggle}
          >
            {collapsed ? (
              <PanelLeftOpen className="size-4" aria-hidden />
            ) : (
              <PanelLeftClose className="size-4" aria-hidden />
            )}
          </button>
        </div>
        <nav aria-label="Principal" className="flex flex-col gap-1">
          <NavLink to="/" end className={linkClass}>
            <Briefcase className="size-4" aria-hidden />
            <span className={label}>Jobs</span>
          </NavLink>
          <NavLink to="/manager" className={linkClass}>
            <BarChart3 className="size-4" aria-hidden />
            <span className={label}>Gerencial</span>
          </NavLink>
          <NavLink to="/fleet" className={linkClass}>
            <Activity className="size-4" aria-hidden />
            <span className={label}>Frota</span>
          </NavLink>

          {simpressEnabled ? (
            <>
              <p className={sectionClass}>
                <span className={label}>Simpress</span>
              </p>
              <NavLink to="/simpress/cnpjs" className={linkClass}>
                <Building2 className="size-4" aria-hidden />
                <span className={label}>CNPJs</span>
              </NavLink>
              <NavLink to="/simpress/contatos" className={linkClass}>
                <Contact className="size-4" aria-hidden />
                <span className={label}>Contatos</span>
              </NavLink>
              <NavLink to="/simpress/sync" className={linkClass}>
                <RefreshCw className="size-4" aria-hidden />
                <span className={label}>Sync</span>
              </NavLink>
              <NavLink to="/simpress/faturas" className={linkClass}>
                <FileText className="size-4" aria-hidden />
                <span className={label}>Faturas</span>
              </NavLink>
              <NavLink to="/simpress/audit" className={linkClass}>
                <ScrollText className="size-4" aria-hidden />
                <span className={label}>Audit</span>
              </NavLink>
            </>
          ) : null}

          <p className={sectionClass}>
            <span className={label}>Configurações</span>
          </p>
          <NavLink to="/settings/printers" className={linkClass}>
            <Printer className="size-4" aria-hidden />
            <span className={label}>Impressoras</span>
          </NavLink>
          <NavLink to="/settings/departments" className={linkClass}>
            <Building2 className="size-4" aria-hidden />
            <span className={label}>Departamentos</span>
          </NavLink>
          <NavLink to="/settings/cost-centers" className={linkClass}>
            <Wallet className="size-4" aria-hidden />
            <span className={label}>Centros de custo</span>
          </NavLink>
          <NavLink to="/settings/cost-rates" className={linkClass}>
            <Coins className="size-4" aria-hidden />
            <span className={label}>Tarifas</span>
          </NavLink>
          <NavLink to="/settings/users" className={linkClass}>
            <Users className="size-4" aria-hidden />
            <span className={label}>Usuários</span>
          </NavLink>
          <NavLink to="/settings/import" className={linkClass}>
            <Upload className="size-4" aria-hidden />
            <span className={label}>Importar CSV</span>
          </NavLink>
        </nav>
      </aside>
    </>
  )
}
