export interface BadgeProps {
  children: string
  variant?: 'default' | 'muted'
}

export function Badge({ children, variant = 'default' }: BadgeProps) {
  return (
    <span
      className={[
        'inline-flex rounded px-2 py-0.5 text-xs font-medium',
        variant === 'muted'
          ? 'bg-[var(--bg-muted)] text-[var(--text-secondary)]'
          : 'bg-[var(--accent-tint)] text-[var(--accent)]',
      ].join(' ')}
    >
      {children}
    </span>
  )
}
