import { useEffect, useMemo, useState } from 'react'
import { useContactCnpjs } from '../../hooks/useSimpressLinks'
import { useSimpressCnpjs } from '../../hooks/useSimpressCnpjs'
import { Button } from '../ui/Button'
import { ErrorBanner } from '../ui/ErrorBanner'

export function ContactCnpjLinksSection({ contactId }: { contactId: number }) {
  const { list: cnpjsList } = useSimpressCnpjs(false)
  const { data, isLoading, isError, refetch, save } = useContactCnpjs(contactId)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [msg, setMsg] = useState<string | null>(null)

  const options = useMemo(() => {
    return (cnpjsList.data ?? [])
      .filter((c) => c.is_active)
      .map((c) => ({ id: c.id, label: `${c.name} (${c.cnpj})` }))
  }, [cnpjsList.data])

  useEffect(() => {
    if (!data) return
    setSelectedIds(new Set(data.map((c) => c.id)))
  }, [data])

  const sortedOptions = useMemo(() => {
    const selected = options.filter((o) => selectedIds.has(o.id))
    const rest = options
      .filter((o) => !selectedIds.has(o.id))
      .sort((a, b) => a.label.localeCompare(b.label, 'pt-BR'))
    return [...selected, ...rest]
  }, [options, selectedIds])

  function toggle(id: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function handleSave() {
    setMsg(null)
    try {
      await save.mutateAsync({ cnpj_ids: [...selectedIds] })
      setMsg('Vínculos salvos.')
    } catch {
      setMsg('Não foi possível salvar. Verifique os campos e tente novamente.')
    }
  }

  if (isError) {
    return (
      <ErrorBanner
        message="Erro ao carregar CNPJs."
        onRetry={() => void refetch()}
      />
    )
  }

  return (
    <div className="mt-4 border-t border-[var(--border-subtle)] pt-4">
      <h3 className="mb-2 text-sm font-semibold text-[var(--text-primary)]">
        CNPJs
      </h3>
      {isLoading || cnpjsList.isLoading ? (
        <p className="text-sm text-[var(--text-secondary)]">Carregando…</p>
      ) : (
        <>
          <div className="max-h-48 space-y-1 overflow-y-auto rounded border border-[var(--border-subtle)] p-2">
            {sortedOptions.length === 0 ? (
              <p className="px-1 py-1 text-sm text-[var(--text-secondary)]">
                Nenhum CNPJ cadastrado.
              </p>
            ) : (
              sortedOptions.map((opt) => (
                <label
                  key={opt.id}
                  className="flex cursor-pointer items-center gap-2 rounded px-1 py-1 text-sm hover:bg-[var(--row-hover)]"
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.has(opt.id)}
                    onChange={() => toggle(opt.id)}
                  />
                  <span className="flex-1">{opt.label}</span>
                </label>
              ))
            )}
          </div>
          <div className="mt-3 flex items-center gap-2">
            <Button
              type="button"
              variant="secondary"
              disabled={save.isPending}
              onClick={() => void handleSave()}
            >
              Salvar vínculos
            </Button>
            {msg ? (
              <span
                className={`text-xs ${msg === 'Vínculos salvos.' ? 'text-[var(--accent)]' : 'text-[var(--text-secondary)]'}`}
              >
                {msg}
              </span>
            ) : null}
          </div>
        </>
      )}
    </div>
  )
}
