import { Printer } from 'lucide-react'
import { useMemo, useState } from 'react'
import { PrinterUsersPanel } from '../../components/settings/PrinterUsersPanel'
import { PageHeader } from '../../components/layout/PageHeader'
import { ConfirmDialog } from '../../components/settings/ConfirmDialog'
import { SettingsSearch } from '../../components/settings/SettingsSearch'
import { MeterReadingDialog } from '../../components/manager/MeterReadingDialog'
import { UnmappedQueuesBanner } from '../../components/settings/UnmappedQueuesBanner'
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
import { usePrintersRegistry } from '../../hooks/usePrintersRegistry'
import type { PrinterCreate, PrinterRead, PrinterUpdate } from '../../types/api'

type FormState = {
  display_name: string
  cups_queue_name: string
  ip_address: string
  manufacturer_model: string
  location: string
  department_id: string
}

const emptyForm = (): FormState => ({
  display_name: '',
  cups_queue_name: '',
  ip_address: '',
  manufacturer_model: '',
  location: '',
  department_id: '',
})

function toForm(p: PrinterRead): FormState {
  return {
    display_name: p.display_name,
    cups_queue_name: p.cups_queue_name,
    ip_address: p.ip_address ?? '',
    manufacturer_model: p.manufacturer_model ?? '',
    location: p.location ?? '',
    department_id: p.department_id != null ? String(p.department_id) : '',
  }
}

export function PrintersPage() {
  const { list, unmapped, create, update, deactivate } = usePrintersRegistry(true)
  const { list: deptList } = useDepartments(false)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<PrinterRead | null>(null)
  const [form, setForm] = useState<FormState>(emptyForm)
  const [confirmId, setConfirmId] = useState<number | null>(null)
  const [meterPrinter, setMeterPrinter] = useState<PrinterRead | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const deptOptions = useMemo(
    () =>
      (deptList.data ?? [])
        .filter((d) => d.is_active)
        .map((d) => ({ value: String(d.id), label: `${d.code} — ${d.name}` })),
    [deptList.data],
  )

  const filtered = useMemo(() => {
    const items = list.data ?? []
    const q = debouncedSearch.trim().toLowerCase()
    if (!q) return items
    return items.filter(
      (p) =>
        p.display_name.toLowerCase().includes(q) ||
        p.cups_queue_name.toLowerCase().includes(q),
    )
  }, [list.data, debouncedSearch])

  function openCreate(prefillQueue?: string) {
    setEditing(null)
    setForm({
      ...emptyForm(),
      cups_queue_name: prefillQueue ?? '',
      display_name: prefillQueue ?? '',
    })
    setFormError(null)
    setDialogOpen(true)
  }

  function openEdit(p: PrinterRead) {
    setEditing(p)
    setForm(toForm(p))
    setFormError(null)
    setDialogOpen(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    const body: PrinterCreate = {
      display_name: form.display_name.trim(),
      cups_queue_name: form.cups_queue_name.trim(),
      ip_address: form.ip_address.trim() || null,
      manufacturer_model: form.manufacturer_model.trim() || null,
      location: form.location.trim() || null,
      department_id: form.department_id ? Number(form.department_id) : null,
    }
    try {
      if (editing) {
        const patch: PrinterUpdate = { ...body }
        await update.mutateAsync({ id: editing.id, body: patch })
        setSuccessMsg('Impressora atualizada.')
      } else {
        await create.mutateAsync(body)
        setSuccessMsg('Impressora cadastrada.')
      }
      setDialogOpen(false)
    } catch {
      setFormError('Não foi possível salvar. Verifique os dados e tente novamente.')
    }
  }

  async function handleDeactivate() {
    if (confirmId == null) return
    try {
      await deactivate.mutateAsync(confirmId)
      setSuccessMsg('Impressora desativada.')
      setConfirmId(null)
    } catch {
      setFormError('Falha ao desativar.')
      setConfirmId(null)
    }
  }

  const saving = create.isPending || update.isPending

  return (
    <>
      <PageHeader
        title="Impressoras"
        actions={
          <Button variant="primary" onClick={() => openCreate()}>
            Nova impressora
          </Button>
        }
      />

      {successMsg ? (
        <div
          role="status"
          className="mb-4 flex items-center justify-between rounded-lg border border-[var(--accent)] bg-[var(--accent-tint)] px-4 py-2 text-sm text-[var(--accent)]"
        >
          <span>{successMsg}</span>
          <button
            type="button"
            className="text-xs underline"
            onClick={() => setSuccessMsg(null)}
          >
            Fechar
          </button>
        </div>
      ) : null}

      <UnmappedQueuesBanner
        queues={unmapped.data ?? []}
        onRegisterQueue={(q) => openCreate(q)}
      />

      <div className="mb-4 flex justify-end">
        <SettingsSearch value={search} onChange={setSearch} placeholder="Buscar impressora…" />
      </div>

      {list.isError ? (
        <ErrorBanner
          message="Não foi possível carregar impressoras."
          onRetry={() => void list.refetch()}
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <div className="max-h-[calc(100vh-320px)] overflow-x-auto overflow-y-auto">
            <table className="w-full min-w-[720px] border-collapse text-sm">
              <thead className="sticky top-0 z-[1] bg-[var(--bg-surface)]">
                <tr className="border-b border-[var(--border-subtle)]">
                  {['Nome', 'Fila no servidor', 'Local', 'Status', 'Ações'].map((h) => (
                    <th
                      key={h}
                      scope="col"
                      className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-[var(--text-secondary)]"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {list.isLoading
                  ? Array.from({ length: 5 }, (_, i) => (
                      <tr key={i} className="border-b border-[var(--border-subtle)]">
                        {Array.from({ length: 5 }, (_, j) => (
                          <td key={j} className="px-3 py-2">
                            <Skeleton className="h-4 w-full max-w-[140px]" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : filtered.length === 0
                    ? (
                        <tr>
                          <td colSpan={5}>
                            <EmptyState
                              icon={<Printer className="mx-auto size-10" />}
                              heading="Nenhuma impressora"
                              body="Cadastre a primeira impressora do registry."
                              actionLabel="Cadastrar primeira impressora"
                              onAction={() => openCreate()}
                            />
                          </td>
                        </tr>
                      )
                    : filtered.map((p, idx) => (
                        <tr
                          key={p.id}
                          className={[
                            'border-b border-[var(--border-subtle)] h-10',
                            idx % 2 === 1 ? 'bg-[var(--bg-muted)]/40' : '',
                          ].join(' ')}
                        >
                          <td className="px-3 py-2 font-medium">{p.display_name}</td>
                          <td className="px-3 py-2 text-[var(--text-secondary)]">
                            {p.cups_queue_name}
                          </td>
                          <td className="px-3 py-2">{p.location ?? '—'}</td>
                          <td className="px-3 py-2">
                            {p.is_active ? (
                              <Badge>Ativa</Badge>
                            ) : (
                              <Badge variant="muted">Inativa</Badge>
                            )}
                          </td>
                          <td className="px-3 py-2">
                            <div className="flex gap-2">
                              <Button
                                variant="ghost"
                                className="min-h-8 px-2 py-1 text-xs"
                                aria-label={`Editar impressora ${p.display_name}`}
                                onClick={() => openEdit(p)}
                              >
                                Editar
                              </Button>
                              {p.is_active ? (
                                <Button
                                  variant="ghost"
                                  className="min-h-8 px-2 py-1 text-xs"
                                  aria-label={`Registrar contador ${p.display_name}`}
                                  onClick={() => setMeterPrinter(p)}
                                >
                                  Contador
                                </Button>
                              ) : null}
                              {p.is_active ? (
                                <Button
                                  variant="ghost"
                                  className="min-h-8 px-2 py-1 text-xs"
                                  aria-label={`Desativar impressora ${p.display_name}`}
                                  onClick={() => setConfirmId(p.id)}
                                >
                                  Desativar
                                </Button>
                              ) : null}
                            </div>
                          </td>
                        </tr>
                      ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        wide
        title={editing ? 'Editar impressora' : 'Nova impressora'}
        footer={
          <>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              type="submit"
              form="printer-form"
              disabled={saving}
            >
              {saving ? 'Salvando…' : 'Salvar'}
            </Button>
          </>
        }
      >
        <form id="printer-form" onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-3">
          {formError ? <ErrorBanner message={formError} /> : null}
          <Input
            label="Nome de exibição"
            required
            value={form.display_name}
            onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
          />
          {(unmapped.data?.length ?? 0) > 0 || editing ? (
            <Select
              label="Fila detectada"
              required={!editing && (unmapped.data?.length ?? 0) > 0}
              options={[
                ...(editing
                  ? [{ value: form.cups_queue_name, label: form.cups_queue_name }]
                  : []),
                ...(unmapped.data ?? []).map((q) => ({ value: q, label: q })),
              ]}
              placeholder="Selecione uma fila…"
              value={form.cups_queue_name}
              onChange={(e) => {
                const q = e.target.value
                setForm((f) => ({
                  ...f,
                  cups_queue_name: q,
                  display_name: f.display_name || q,
                }))
              }}
            />
          ) : null}
          <details className="rounded border border-[var(--border-subtle)] p-3">
            <summary className="cursor-pointer text-sm font-medium">Avançado</summary>
            <div className="mt-3">
              <Input
                label="Identificador no servidor"
                value={form.cups_queue_name}
                onChange={(e) =>
                  setForm((f) => ({ ...f, cups_queue_name: e.target.value }))
                }
                placeholder="nome exato da fila no servidor"
              />
            </div>
          </details>
          <Input
            label="Endereço IP"
            value={form.ip_address}
            onChange={(e) => setForm((f) => ({ ...f, ip_address: e.target.value }))}
          />
          <Input
            label="Fabricante / modelo"
            value={form.manufacturer_model}
            onChange={(e) => setForm((f) => ({ ...f, manufacturer_model: e.target.value }))}
          />
          <Input
            label="Localização"
            value={form.location}
            onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
          />
          <Select
            label="Departamento"
            options={deptOptions}
            placeholder="Nenhum"
            value={form.department_id}
            onChange={(e) => setForm((f) => ({ ...f, department_id: e.target.value }))}
          />
          {editing ? <PrinterUsersPanel printerId={editing.id} /> : null}
        </form>
      </Dialog>

      <ConfirmDialog
        open={confirmId != null}
        title="Desativar impressora"
        message="A impressora será marcada como inativa (soft-delete). Jobs históricos permanecem."
        loading={deactivate.isPending}
        onConfirm={() => void handleDeactivate()}
        onClose={() => setConfirmId(null)}
      />

      {meterPrinter ? (
        <MeterReadingDialog
          printerId={meterPrinter.id}
          printerName={meterPrinter.display_name}
          open
          onClose={() => setMeterPrinter(null)}
        />
      ) : null}
    </>
  )
}
