export interface BadgeProps {
  children: string
  variant?: 'default' | 'muted' | 'warning'
  title?: string
}

export function Badge({ children, variant = 'default', title }: BadgeProps) {
  return (
    <span
      title={title}
      className={[
        'inline-flex rounded px-2 py-0.5 text-xs font-medium',
        variant === 'muted'
          ? 'bg-[var(--bg-muted)] text-[var(--text-secondary)]'
          : variant === 'warning'
            ? 'bg-[#FFF8E6] text-[#8A6D00]'
            : 'bg-[var(--accent-tint)] text-[var(--accent)]',
      ].join(' ')}
    >
      {children}
    </span>
  )
}
