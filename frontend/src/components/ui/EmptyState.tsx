import type { ReactNode } from 'react'
import { Button } from './Button'

export interface EmptyStateProps {
  heading: string
  body?: string
  icon?: ReactNode
  actionLabel?: string
  onAction?: () => void
}

export function EmptyState({
  heading,
  body,
  icon,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
      {icon ? <div className="mb-4 text-[var(--text-tertiary)]">{icon}</div> : null}
      <h3 className="text-[17px] font-semibold text-[var(--text-primary)]">{heading}</h3>
      {body ? (
        <p className="mt-2 max-w-md text-sm text-[var(--text-secondary)]">{body}</p>
      ) : null}
      {actionLabel && onAction ? (
        <Button variant="ghost" onClick={onAction} className="mt-4">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  )
}
