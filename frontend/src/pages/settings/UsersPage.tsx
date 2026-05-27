import { Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { UserPrinterAccessSection } from '../../components/settings/UserPrinterAccessSection'
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
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { useDepartments } from '../../hooks/useDepartments'
import { useCostCenters } from '../../hooks/useCostCenters'
import { useUsers } from '../../hooks/useUsers'
import type { UserCreate, UserRead, UserUpdate } from '../../types/api'

export function UsersPage() {
  const { list, create, update, deactivate } = useUsers(false)
  const { list: deptList } = useDepartments(false)
  const { list: ccList } = useCostCenters(false)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<UserRead | null>(null)
  const [cupsUsername, setCupsUsername] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [departmentId, setDepartmentId] = useState('')
  const [costCenterId, setCostCenterId] = useState('')
  const [confirmId, setConfirmId] = useState<number | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const deptOptions = useMemo(
    () =>
      (deptList.data ?? [])
        .filter((d) => d.is_active)
        .map((d) => ({ value: String(d.id), label: `${d.code} — ${d.name}` })),
    [deptList.data],
  )

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
      (u) =>
        u.cups_username.toLowerCase().includes(q) ||
        u.display_name.toLowerCase().includes(q),
    )
  }, [list.data, debouncedSearch])

  function openCreate() {
    setEditing(null)
    setCupsUsername('')
    setDisplayName('')
    setDepartmentId('')
    setCostCenterId('')
    setFormError(null)
    setDialogOpen(true)
  }

  function openEdit(u: UserRead) {
    setEditing(u)
    setCupsUsername(u.cups_username)
    setDisplayName(u.display_name)
    setDepartmentId(String(u.department_id))
    setCostCenterId(u.cost_center_id != null ? String(u.cost_center_id) : '')
    setFormError(null)
    setDialogOpen(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!departmentId) {
      setFormError('Selecione um departamento.')
      return
    }
    try {
      if (editing) {
        const patch: UserUpdate = {
          display_name: displayName.trim(),
          department_id: Number(departmentId),
          cost_center_id: costCenterId ? Number(costCenterId) : null,
        }
        await update.mutateAsync({ id: editing.id, body: patch })
        setSuccessMsg('Usuário atualizado.')
      } else {
        const body: UserCreate = {
          cups_username: cupsUsername.trim(),
          display_name: displayName.trim(),
          department_id: Number(departmentId),
          cost_center_id: costCenterId ? Number(costCenterId) : null,
        }
        const created = await create.mutateAsync(body)
        setEditing(created)
        setSuccessMsg('Usuário cadastrado. Configure as impressoras abaixo.')
        return
      }
      setDialogOpen(false)
    } catch {
      setFormError('Não foi possível salvar.')
    }
  }

  return (
    <>
      <PageHeader
        title="Usuários"
        actions={
          <Button variant="primary" onClick={openCreate}>
            Novo usuário
          </Button>
        }
      />
      {successMsg ? (
        <div className="mb-4 rounded-lg border border-[var(--accent)] bg-[var(--accent-tint)] px-4 py-2 text-sm text-[var(--accent)]">
          {successMsg}
        </div>
      ) : null}
      <div className="mb-4 flex justify-end">
        <SettingsSearch value={search} onChange={setSearch} placeholder="Buscar usuário…" />
      </div>
      {list.isError ? (
        <ErrorBanner message="Erro ao carregar usuários." onRetry={() => void list.refetch()} />
      ) : (
        <div className="overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-[var(--border-subtle)]">
                {['Usuário CUPS', 'Nome', 'Status', 'Ações'].map((h) => (
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
                          <Skeleton className="h-4 w-28" />
                        </td>
                      ))}
                    </tr>
                  ))
                : filtered.length === 0
                  ? (
                      <tr>
                        <td colSpan={4}>
                          <EmptyState
                            icon={<Users className="mx-auto size-10" />}
                            heading="Nenhum usuário"
                            actionLabel="Cadastrar primeiro usuário"
                            onAction={openCreate}
                          />
                        </td>
                      </tr>
                    )
                  : filtered.map((u, idx) => (
                      <tr key={u.id} className={idx % 2 === 1 ? 'bg-[var(--bg-muted)]/40' : ''}>
                        <td className="px-3 py-2 font-mono text-xs">{u.cups_username}</td>
                        <td className="px-3 py-2">{u.display_name}</td>
                        <td className="px-3 py-2">
                          {u.is_active ? <Badge>Ativo</Badge> : <Badge variant="muted">Inativo</Badge>}
                        </td>
                        <td className="px-3 py-2 flex gap-2">
                          <Button variant="ghost" className="min-h-8 px-2 text-xs" onClick={() => openEdit(u)}>
                            Editar
                          </Button>
                          {u.is_active ? (
                            <Button variant="ghost" className="min-h-8 px-2 text-xs" onClick={() => setConfirmId(u.id)}>
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
        wide={!!editing}
        title={editing ? 'Editar usuário' : 'Novo usuário'}
        footer={
          <>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>Cancelar</Button>
            <Button variant="primary" type="submit" form="user-form" disabled={create.isPending || update.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form id="user-form" onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-3">
          {formError ? <ErrorBanner message={formError} /> : null}
          <Input
            label="Usuário CUPS"
            required
            readOnly={!!editing}
            value={cupsUsername}
            onChange={(e) => setCupsUsername(e.target.value)}
          />
          <Input
            label="Nome de exibição"
            required
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
          <Select
            label="Departamento"
            required
            options={deptOptions}
            placeholder="Selecione…"
            value={departmentId}
            onChange={(e) => setDepartmentId(e.target.value)}
          />
          <Select
            label="Centro de custo (override)"
            options={ccOptions}
            placeholder="Herdar do departamento"
            value={costCenterId}
            onChange={(e) => setCostCenterId(e.target.value)}
          />
          {editing ? (
            <>
              <div className="flex flex-wrap gap-3 print:hidden">
                <Link
                  to={`/settings/users/${editing.id}/ti-export`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-[var(--accent)] underline"
                >
                  Exportar roteiro TI
                </Link>
              </div>
              <UserPrinterAccessSection userId={editing.id} />
            </>
          ) : (
            <p className="text-xs text-[var(--text-secondary)]">
              Salve o usuário para configurar impressoras permitidas.
            </p>
          )}
        </form>
      </Dialog>
      <ConfirmDialog
        open={confirmId != null}
        title="Desativar usuário"
        message="O usuário será marcado como inativo."
        loading={deactivate.isPending}
        onConfirm={() => {
          if (confirmId != null) {
            void deactivate.mutateAsync(confirmId).then(() => {
              setSuccessMsg('Usuário desativado.')
              setConfirmId(null)
            })
          }
        }}
        onClose={() => setConfirmId(null)}
      />
    </>
  )
}
