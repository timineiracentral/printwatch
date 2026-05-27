import type { ButtonHTMLAttributes } from 'react'

export type ButtonVariant = 'secondary' | 'ghost'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
}

const variantClasses: Record<ButtonVariant, string> = {
  secondary:
    'border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-primary)] hover:bg-[var(--row-hover)]',
  ghost:
    'border border-transparent bg-transparent text-[var(--text-secondary)] hover:bg-[var(--row-hover)] hover:text-[var(--text-primary)]',
}

export function Button({
  variant = 'secondary',
  className = '',
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={[
        'inline-flex min-h-11 items-center justify-center rounded-lg px-4 py-2 text-sm font-medium',
        'transition-colors duration-150',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]',
        'disabled:cursor-not-allowed disabled:opacity-50',
        variantClasses[variant],
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...props}
    />
  )
}
