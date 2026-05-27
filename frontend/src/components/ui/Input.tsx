import type { InputHTMLAttributes } from 'react'
import { useId } from 'react'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
}

export function Input({ label, id: idProp, className = '', ...props }: InputProps) {
  const autoId = useId()
  const id = idProp ?? autoId

  const input = (
    <input
      id={id}
      className={[
        'min-h-11 w-full rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-2 text-sm text-[var(--text-primary)]',
        'placeholder:text-[var(--text-tertiary)]',
        'transition-colors duration-150',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...props}
    />
  )

  if (!label) {
    return input
  }

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-xs text-[var(--text-secondary)]">
        {label}
      </label>
      {input}
    </div>
  )
}
