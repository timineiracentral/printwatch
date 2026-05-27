import type { SelectHTMLAttributes } from 'react'
import { useId } from 'react'

export interface SelectOption {
  value: string
  label: string
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  options: SelectOption[]
  placeholder?: string
}

export function Select({
  label,
  options,
  placeholder,
  id: idProp,
  className = '',
  ...props
}: SelectProps) {
  const autoId = useId()
  const id = idProp ?? autoId

  const select = (
    <select
      id={id}
      className={[
        'min-h-11 w-full rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-2 text-sm text-[var(--text-primary)]',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...props}
    >
      {placeholder ? (
        <option value="">{placeholder}</option>
      ) : null}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )

  if (!label) return select

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-xs text-[var(--text-secondary)]">
        {label}
      </label>
      {select}
    </div>
  )
}
