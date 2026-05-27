import { useEffect, useState } from 'react'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { useUrlFilters } from '../../hooks/useUrlFilters'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { DatePresetGroup } from './DatePresetGroup'
import { PrinterCombobox } from './PrinterCombobox'

/**
 * Preset "Mês atual" nos filtros da tabela (date_from → hoje) é independente do
 * bucket `stats.mes` nos cards de sumário — mesma API, janelas diferentes.
 */
export function FilterBar() {
  const { filters, setFilters, clearFilters, applyDatePreset } = useUrlFilters()
  const [searchLocal, setSearchLocal] = useState(filters.search ?? '')
  const debouncedSearch = useDebouncedValue(searchLocal, 300)

  useEffect(() => {
    setSearchLocal(filters.search ?? '')
  }, [filters.search])

  useEffect(() => {
    const next = debouncedSearch.trim()
    const current = filters.search?.trim() ?? ''
    if (next !== current) {
      setFilters({ search: next || undefined })
    }
  }, [debouncedSearch, filters.search, setFilters])

  return (
    <section
      className="flex flex-col gap-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4"
      aria-label="Filtros"
    >
      <div className="flex flex-wrap items-center gap-4">
        <DatePresetGroup filters={filters} onPreset={applyDatePreset} />
        <Button variant="ghost" type="button" onClick={clearFilters} className="ml-auto">
          Limpar filtros
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <Input
          label="De"
          type="date"
          value={filters.date_from ?? ''}
          onChange={(e) =>
            setFilters({ date_from: e.target.value || undefined })
          }
        />
        <Input
          label="Até"
          type="date"
          value={filters.date_to ?? ''}
          onChange={(e) =>
            setFilters({ date_to: e.target.value || undefined })
          }
        />
        <Input
          label="Usuário"
          placeholder="Filtrar por usuário…"
          value={filters.username ?? ''}
          onChange={(e) =>
            setFilters({ username: e.target.value || undefined })
          }
        />
        <div className="flex flex-col gap-1">
          <span className="text-xs text-[var(--text-secondary)]">Impressora</span>
          <PrinterCombobox
            value={filters.printer}
            onChange={(printer) => setFilters({ printer })}
          />
        </div>
        <Input
          label="Arquivo"
          placeholder="Buscar por nome do arquivo…"
          value={searchLocal}
          onChange={(e) => setSearchLocal(e.target.value)}
        />
      </div>
    </section>
  )
}
