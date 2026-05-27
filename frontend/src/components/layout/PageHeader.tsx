import type { ReactNode } from 'react'

export interface PageHeaderProps {
  title: string
  actions?: ReactNode
}

export function PageHeader({ title, actions }: PageHeaderProps) {
  return (
    <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
      <h1 className="text-2xl font-semibold leading-tight text-[var(--text-primary)]">{title}</h1>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </header>
  )
}
