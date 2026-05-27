import { useState, type ReactNode } from 'react'
import { Sidebar } from './Sidebar'

export interface AppShellProps {
  header: ReactNode
  children: ReactNode
}

export function AppShell({ header, children }: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex min-h-screen bg-[var(--bg-canvas)]">
      <Sidebar
        mobileOpen={mobileOpen}
        onMobileToggle={() => setMobileOpen((open) => !open)}
      />
      <div className="flex min-w-0 flex-1 flex-col lg:pl-0">
        <main className="mx-auto w-full max-w-[1400px] flex-1 px-6 py-5 pt-16 lg:px-6 lg:py-6 lg:pt-6">
          {header}
          {children}
        </main>
      </div>
    </div>
  )
}
