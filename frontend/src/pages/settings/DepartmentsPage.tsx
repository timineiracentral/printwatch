import { Building2 } from 'lucide-react'
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
import { Select } from '../../components/ui/Select'
import { Skeleton } from '../../components/ui/Skeleton'
import { useCostCenters } from '../../hooks/useCostCenters'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { useDepartments } from '../../hooks/useDepartments'
import { normalizeOrgCode } from '../../lib/normalize'
import type { DepartmentCreate, DepartmentRead, DepartmentUpdate } from '../../types/api'

export function DepartmentsPage() {
  const { list, create, update, deactivate } = useDepartments(false)
  const { list: ccList } = useCostCenters(false)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<DepartmentRead | null>(null)
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [costCenterId, setCostCenterId] = useState('')
  const [confirmId, setConfirmId] = useState<number | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const ccOptions = useMemo(
    () =>
      (ccList.data ?? [])
        .filter((c) => c.is_active)
        .map((c) => ({ value: String(c.id), label: `${c.code} — ${c.name}` })),
    [ccList.data],
  )

  const filtered = useMemo(() => {
    const items = list.data ?? []
    const q = debouncedSearch.trim().toLowerCase()
    if (!q) return items
    return items.filter(
      (d) =>
        d.code.toLowerCase().includes(q) || d.name.toLowerCase().includes(q),
    )
  }, [list.data, debouncedSearch])

  function openCreate() {
    setEditing(null)
    setCode('')
    setName('')
    setCostCenterId('')
    setFormError(null)
    setDialogOpen(true)
  }

  function openEdit(d: DepartmentRead) {
    setEditing(d)
    setCode(d.code)
    setName(d.name)
    setCostCenterId(d.cost_center_id != null ? String(d.cost_center_id) : '')
    setFormError(null)
    setDialogOpen(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    const payload: DepartmentCreate = {
      code: normalizeOrgCode(code),
      name: name.trim(),
      cost_center_id: costCenterId ? Number(costCenterId) : null,
    }
    try {
      if (editing) {
        const patch: DepartmentUpdate = payload
        await update.mutateAsync({ id: editing.id, body: patch })
        setSuccessMsg('Departamento atualizado.')
      } else {
        await create.mutateAsync(payload)
        setSuccessMsg('Departamento cadastrado.')
      }
      setDialogOpen(false)
    } catch {
      setFormError('Não foi possível salvar.')
    }
  }

  const saving = create.isPending || update.isPending

  return (
    <>
      <PageHeader
        title="Departamentos"
        actions={
          <Button variant="primary" onClick={openCreate}>
            Novo departamento
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
        <ErrorBanner message="Erro ao carregar departamentos." onRetry={() => void list.refetch()} />
      ) : (
        <div className="overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <table className="w-full min-w-[560px] text-sm">
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
                            icon={<Building2 className="mx-auto size-10" />}
                            heading="Nenhum departamento"
                            actionLabel="Cadastrar primeiro departamento"
                            onAction={openCreate}
                          />
                        </td>
                      </tr>
                    )
                  : filtered.map((d, idx) => (
                      <tr
                        key={d.id}
                        className={idx % 2 === 1 ? 'bg-[var(--bg-muted)]/40' : ''}
                      >
                        <td className="px-3 py-2 font-mono text-xs">{d.code}</td>
                        <td className="px-3 py-2">{d.name}</td>
                        <td className="px-3 py-2">
                          {d.is_active ? <Badge>Ativo</Badge> : <Badge variant="muted">Inativo</Badge>}
                        </td>
                        <td className="px-3 py-2 flex gap-2">
                          <Button variant="ghost" className="min-h-8 px-2 text-xs" onClick={() => openEdit(d)}>
                            Editar
                          </Button>
                          {d.is_active ? (
                            <Button variant="ghost" className="min-h-8 px-2 text-xs" onClick={() => setConfirmId(d.id)}>
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
        title={editing ? 'Editar departamento' : 'Novo departamento'}
        footer={
          <>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>Cancelar</Button>
            <Button variant="primary" type="submit" form="dept-form" disabled={saving}>
              Salvar
            </Button>
          </>
        }
      >
        <form id="dept-form" onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-3">
          {formError ? <ErrorBanner message={formError} /> : null}
          <Input
            label="Código"
            required
            value={code}
            onChange={(e) => setCode(normalizeOrgCode(e.target.value))}
          />
          <Input label="Nome" required value={name} onChange={(e) => setName(e.target.value)} />
          <Select
            label="Centro de custo"
            options={ccOptions}
            placeholder="Nenhum"
            value={costCenterId}
            onChange={(e) => setCostCenterId(e.target.value)}
          />
        </form>
      </Dialog>
      <ConfirmDialog
        open={confirmId != null}
        title="Desativar departamento"
        message="O departamento será marcado como inativo."
        loading={deactivate.isPending}
        onConfirm={() => {
          if (confirmId != null) {
            void deactivate.mutateAsync(confirmId).then(() => {
              setSuccessMsg('Departamento desativado.')
              setConfirmId(null)
            })
          }
        }}
        onClose={() => setConfirmId(null)}
      />
    </>
  )
}
