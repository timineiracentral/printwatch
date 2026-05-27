import { Wallet } from 'lucide-react'
import { useMemo, useState } from 'react'
import { PageHeader } from '../../components/layout/PageHeader'
import { ConfirmDialog } from '../../components/settings/ConfirmDialog'
import { SettingsSearch } from '../../components/settings/SettingsSearch'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Dialog } from '../../components/ui/Dialog'
import { EmptyState } from '../../components/ui/EmptyState'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import { Input } from '../../components/ui/Input'
import { Skeleton } from '../../components/ui/Skeleton'
import { useCostCenters } from '../../hooks/useCostCenters'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { normalizeOrgCode } from '../../lib/normalize'
import type { CostCenterCreate, CostCenterRead, CostCenterUpdate } from '../../types/api'

export function CostCentersPage() {
  const { list, create, update, deactivate } = useCostCenters(false)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<CostCenterRead | null>(null)
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [confirmId, setConfirmId] = useState<number | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const filtered = useMemo(() => {
    const items = list.data ?? []
    const q = debouncedSearch.trim().toLowerCase()
    if (!q) return items
    return items.filter(
      (c) =>
        c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q),
    )
  }, [list.data, debouncedSearch])

  function openCreate() {
    setEditing(null)
    setCode('')
    setName('')
    setFormError(null)
    setDialogOpen(true)
  }

  function openEdit(c: CostCenterRead) {
    setEditing(c)
    setCode(c.code)
    setName(c.name)
    setFormError(null)
    setDialogOpen(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload: CostCenterCreate = {
      code: normalizeOrgCode(code),
      name: name.trim(),
    }
    try {
      if (editing) {
        await update.mutateAsync({ id: editing.id, body: payload as CostCenterUpdate })
        setSuccessMsg('Centro de custo atualizado.')
      } else {
        await create.mutateAsync(payload)
        setSuccessMsg('Centro de custo cadastrado.')
      }
      setDialogOpen(false)
    } catch {
      setFormError('Não foi possível salvar.')
    }
  }

  return (
    <>
      <PageHeader
        title="Centros de custo"
        actions={
          <Button variant="primary" onClick={openCreate}>
            Novo centro de custo
          </Button>
        }
      />
      {successMsg ? (
        <div className="mb-4 rounded-lg border border-[var(--accent)] bg-[var(--accent-tint)] px-4 py-2 text-sm text-[var(--accent)]">
          {successMsg}
        </div>
      ) : null}
      <div className="mb-4 flex justify-end">
        <SettingsSearch value={search} onChange={setSearch} />
      </div>
      {list.isError ? (
        <ErrorBanner message="Erro ao carregar centros de custo." onRetry={() => void list.refetch()} />
      ) : (
        <div className="overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-subtle)]">
                {['Código', 'Nome', 'Status', 'Ações'].map((h) => (
                  <th key={h} scope="col" className="px-3 py-2 text-left text-xs font-medium uppercase text-[var(--text-secondary)]">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {list.isLoading
                ? Array.from({ length: 5 }, (_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 4 }, (_, j) => (
                        <td key={j} className="px-3 py-2">
                          <Skeleton className="h-4 w-24" />
                        </td>
                      ))}
                    </tr>
                  ))
                : filtered.length === 0
                  ? (
                      <tr>
                        <td colSpan={4}>
                          <EmptyState
                            icon={<Wallet className="mx-auto size-10" />}
                            heading="Nenhum centro de custo"
                            actionLabel="Cadastrar primeiro centro"
                            onAction={openCreate}
                          />
                        </td>
                      </tr>
                    )
                  : filtered.map((c, idx) => (
                      <tr key={c.id} className={idx % 2 === 1 ? 'bg-[var(--bg-muted)]/40' : ''}>
                        <td className="px-3 py-2 font-mono text-xs">{c.code}</td>
                        <td className="px-3 py-2">{c.name}</td>
                        <td className="px-3 py-2">
                          {c.is_active ? <Badge>Ativo</Badge> : <Badge variant="muted">Inativo</Badge>}
                        </td>
                        <td className="px-3 py-2 flex gap-2">
                          <Button variant="ghost" className="min-h-8 px-2 text-xs" onClick={() => openEdit(c)}>
                            Editar
                          </Button>
                          {c.is_active ? (
                            <Button variant="ghost" className="min-h-8 px-2 text-xs" onClick={() => setConfirmId(c.id)}>
                              Desativar
                            </Button>
                          ) : null}
                        </td>
                      </tr>
                    ))}
            </tbody>
          </table>
        </div>
      )}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? 'Editar centro de custo' : 'Novo centro de custo'}
        footer={
          <>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>Cancelar</Button>
            <Button variant="primary" type="submit" form="cc-form" disabled={create.isPending || update.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form id="cc-form" onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-3">
          {formError ? <ErrorBanner message={formError} /> : null}
          <Input label="Código" required value={code} onChange={(e) => setCode(normalizeOrgCode(e.target.value))} />
          <Input label="Nome" required value={name} onChange={(e) => setName(e.target.value)} />
        </form>
      </Dialog>
      <ConfirmDialog
        open={confirmId != null}
        title="Desativar centro de custo"
        message="O centro será marcado como inativo."
        loading={deactivate.isPending}
        onConfirm={() => {
          if (confirmId != null) {
            void deactivate.mutateAsync(confirmId).then(() => {
              setSuccessMsg('Centro desativado.')
              setConfirmId(null)
            })
          }
        }}
        onClose={() => setConfirmId(null)}
      />
    </>
  )
}
