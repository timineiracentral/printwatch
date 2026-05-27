import { useEffect, useMemo, useState } from 'react'
import { usePrintersRegistry } from '../../hooks/usePrintersRegistry'
import { useUserPrinterAccess } from '../../hooks/useUserPrinterAccess'
import type { PrinterAccessItem } from '../../types/api'
import { Button } from '../ui/Button'
import { ErrorBanner } from '../ui/ErrorBanner'

type LocalAssignment = PrinterAccessItem & { label: string }

export function UserPrinterAccessSection({ userId }: { userId: number }) {
  const { list: printersList } = usePrintersRegistry(true)
  const { data, isLoading, isError, refetch, save } = useUserPrinterAccess(userId)
  const [local, setLocal] = useState<LocalAssignment[]>([])
  const [msg, setMsg] = useState<string | null>(null)

  const printerOptions = useMemo(() => {
    const active = (printersList.data ?? []).filter((p) => p.is_active)
    return active.map((p) => ({
      id: p.id,
      label: p.location ? `${p.display_name} — ${p.location}` : p.display_name,
    }))
  }, [printersList.data])

  useEffect(() => {
    if (!data) return
    const byId = new Map(printerOptions.map((o) => [o.id, o.label]))
    setLocal(
      data
        .filter((r) => r.is_active)
        .map((r) => ({
          printer_id: r.printer_id,
          is_default: r.is_default,
          is_active: true,
          label: r.printer_display_name ?? byId.get(r.printer_id) ?? `#${r.printer_id}`,
        })),
    )
  }, [data, printerOptions])

  function togglePrinter(printerId: number, label: string) {
    setLocal((prev) => {
      const exists = prev.find((a) => a.printer_id === printerId)
      if (exists) {
        const next = prev.filter((a) => a.printer_id !== printerId)
        if (exists.is_default && next.length > 0 && !next.some((a) => a.is_default)) {
          next[0] = { ...next[0], is_default: true }
        }
        return next
      }
      return [
        ...prev,
        {
          printer_id: printerId,
          is_default: prev.length === 0,
          is_active: true,
          label,
        },
      ]
    })
  }

  function setDefault(printerId: number) {
    setLocal((prev) =>
      prev.map((a) => ({ ...a, is_default: a.printer_id === printerId })),
    )
  }

  async function handleSave() {
    setMsg(null)
    try {
      await save.mutateAsync({
        assignments: local.map(({ printer_id, is_default, is_active }) => ({
          printer_id,
          is_default,
          is_active,
        })),
      })
      setMsg('Impressoras salvas.')
    } catch {
      setMsg('Falha ao salvar impressoras.')
    }
  }

  const selectedIds = new Set(local.map((a) => a.printer_id))
  const sortedOptions = useMemo(() => {
    const selected = printerOptions.filter((o) => selectedIds.has(o.id))
    const rest = printerOptions
      .filter((o) => !selectedIds.has(o.id))
      .sort((a, b) => a.label.localeCompare(b.label, 'pt-BR'))
    return [...selected, ...rest]
  }, [printerOptions, selectedIds])

  if (isError) {
    return (
      <ErrorBanner
        message="Não foi possível carregar impressoras permitidas."
        onRetry={() => void refetch()}
      />
    )
  }

  return (
    <div className="mt-4 border-t border-[var(--border-subtle)] pt-4">
      <h3 className="mb-2 text-sm font-semibold text-[var(--text-primary)]">
        Impressoras permitidas
      </h3>
      {isLoading ? (
        <p className="text-sm text-[var(--text-secondary)]">Carregando…</p>
      ) : (
        <>
          {local.length > 10 ? (
            <p className="mb-2 text-xs text-[var(--text-secondary)]">
              Este usuário tem mais de 10 impressoras — revise se todas são necessárias.
            </p>
          ) : null}
          <div className="max-h-48 space-y-1 overflow-y-auto rounded border border-[var(--border-subtle)] p-2">
            {sortedOptions.map((opt) => (
              <label
                key={opt.id}
                className="flex cursor-pointer items-center gap-2 rounded px-1 py-1 text-sm hover:bg-[var(--row-hover)]"
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(opt.id)}
                  onChange={() => togglePrinter(opt.id, opt.label)}
                />
                <span className="flex-1">{opt.label}</span>
                {selectedIds.has(opt.id) ? (
                  <button
                    type="button"
                    className="text-xs text-[var(--accent)] underline"
                    onClick={() => setDefault(opt.id)}
                  >
                    {local.find((a) => a.printer_id === opt.id)?.is_default
                      ? 'Padrão'
                      : 'Definir padrão'}
                  </button>
                ) : null}
              </label>
            ))}
          </div>
          <div className="mt-3 flex items-center gap-2">
            <Button
              type="button"
              variant="secondary"
              disabled={save.isPending}
              onClick={() => void handleSave()}
            >
              Salvar impressoras
            </Button>
            {msg ? <span className="text-xs text-[var(--text-secondary)]">{msg}</span> : null}
          </div>
        </>
      )}
    </div>
  )
}
