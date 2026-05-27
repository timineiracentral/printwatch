import {
  Combobox,
  ComboboxButton,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from '@headlessui/react'
import { ChevronDown, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { usePrinters } from '../../hooks/usePrinters'

export interface PrinterComboboxProps {
  value?: string
  onChange: (printer: string | undefined) => void
}

export function PrinterCombobox({ value, onChange }: PrinterComboboxProps) {
  const { data: printers = [], isLoading } = usePrinters()
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return printers
    return printers.filter((name) => name.toLowerCase().includes(q))
  }, [printers, query])

  return (
    <Combobox
      value={value ?? null}
      onChange={(next: string | null) => {
        onChange(next ?? undefined)
        setQuery('')
      }}
      nullable
    >
      <div className="relative">
        <ComboboxInput
          className={[
            'min-h-11 w-full rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] py-2 pl-3 pr-16 text-sm text-[var(--text-primary)]',
            'placeholder:text-[var(--text-tertiary)]',
            'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]',
          ].join(' ')}
          displayValue={(name: string | null) => name ?? ''}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Selecionar impressora…"
          aria-label="Impressora"
        />
        <div className="absolute inset-y-0 right-0 flex items-center gap-0.5 pr-2">
          {value ? (
            <button
              type="button"
              className="rounded p-1 text-[var(--text-tertiary)] hover:bg-[var(--row-hover)] hover:text-[var(--text-primary)]"
              aria-label="Limpar impressora"
              onClick={() => {
                onChange(undefined)
                setQuery('')
              }}
            >
              <X className="size-4" aria-hidden />
            </button>
          ) : null}
          <ComboboxButton className="rounded p-1 text-[var(--text-tertiary)] hover:text-[var(--text-primary)]">
            <ChevronDown className="size-4" aria-hidden />
          </ComboboxButton>
        </div>
        <ComboboxOptions
          className={[
            'absolute z-20 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-[var(--border)]',
            'bg-[var(--bg-surface)] py-1 shadow-[0_4px_16px_rgba(0,0,0,0.08)]',
            'empty:invisible',
          ].join(' ')}
        >
          {isLoading ? (
            <div className="px-3 py-2 text-sm text-[var(--text-secondary)]">
              Carregando…
            </div>
          ) : filtered.length === 0 ? (
            <div className="px-3 py-2 text-sm text-[var(--text-secondary)]">
              Nenhuma impressora encontrada
            </div>
          ) : (
            filtered.map((name) => (
              <ComboboxOption
                key={name}
                value={name}
                className="cursor-pointer px-3 py-2 text-sm text-[var(--text-primary)] data-focus:bg-[var(--accent-tint)] data-focus:text-[var(--accent)]"
              >
                {name}
              </ComboboxOption>
            ))
          )}
        </ComboboxOptions>
      </div>
    </Combobox>
  )
}
