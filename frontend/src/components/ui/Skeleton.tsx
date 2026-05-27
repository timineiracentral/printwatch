import type { HTMLAttributes } from 'react'

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {}

export function Skeleton({ className = '', ...props }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-hidden="true"
      className={['skeleton-pulse rounded-md bg-[var(--border-subtle)]', className]
        .filter(Boolean)
        .join(' ')}
      {...props}
    />
  )
}
