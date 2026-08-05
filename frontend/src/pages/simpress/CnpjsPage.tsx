import { Building2 } from 'lucide-react'
import { useMemo, useState } from 'react'
import { CnpjContactLinksSection } from '../../components/simpress/CnpjContactLinksSection'
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
import { useSimpressCnpjs } from '../../hooks/useSimpressCnpjs'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { isValidCnpj, normalizeCnpj } from '../../lib/simpressCnpj'
import type { CnpjCreate, CnpjRead, CnpjUpdate } from '../../types/api'

export function CnpjsPage() {
  const { list, create, update, deactivate } = useSimpressCnpjs(false)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<CnpjRead | null>(null)
  const [cnpj, setCnpj] = useState('')
  const [name, setName] = useState('')
  const [confirmId, setConfirmId] = useState<number | null>(null)
  const [confirmError, setConfirmError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const filtered = useMemo(() => {
    const items = list.data ?? []
    const q = debouncedSearch.trim().toLowerCase()
    if (!q) return items
    return items.filter(
      (c) =>
        c.cnpj.includes(q.replace(/\D/g, '')) ||
        c.name.toLowerCase().includes(q),
    )
  }, [list.data, debouncedSearch])

  function openCreate() {
    setEditing(null)
    setCnpj('')
    setName('')
    setFormError(null)
    setDialogOpen(true)
  }

  function openEdit(c: CnpjRead) {
    setEditing(c)
    setCnpj(c.cnpj)
    setName(c.name)
    setFormError(null)
    setDialogOpen(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const digits = normalizeCnpj(cnpj)
    if (!isValidCnpj(digits)) {
      setFormError('Informe um CNPJ válido com 14 dígitos.')
      return
    }
    const trimmedName = name.trim()
    if (!trimmedName) {
      setFormError('Não foi possível salvar. Verifique os campos e tente novamente.')
      return
    }
    const payload: CnpjCreate = { cnpj: digits, name: trimmedName }
    try {
      if (editing) {
        await update.mutateAsync({ id: editing.id, body: payload as CnpjUpdate })
        setSuccessMsg('CNPJ atualizado.')
      } else {
        await create.mutateAsync(payload)
        setSuccessMsg('CNPJ cadastrado.')
      }
      setDialogOpen(false)
    } catch {
      setFormError('Não foi possível salvar. Verifique os campos e tente novamente.')
    }
  }

  return (
    <>
      <PageHeader
        title="CNPJs"
        actions={
          <Button variant="primary" onClick={openCreate}>
            Novo CNPJ
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
        <ErrorBanner message="Erro ao carregar CNPJs." onRetry={() => void list.refetch()} />
      ) : (
        <div className="overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-subtle)]">
                {['CNPJ', 'Nome', 'Status', 'Ações'].map((h) => (
                  <th
                    key={h}
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium uppercase text-[var(--text-secondary)]"
                  >
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
                            heading="Nenhum CNPJ"
                            body="Cadastre o primeiro CNPJ para associar contatos WhatsApp."
                            actionLabel="Cadastrar primeiro CNPJ"
                            onAction={openCreate}
                          />
                        </td>
                      </tr>
                    )
                  : filtered.map((c, idx) => (
                      <tr key={c.id} className={idx % 2 === 1 ? 'bg-[var(--bg-muted)]/40' : ''}>
                        <td className="px-3 py-2 font-mono text-xs">{c.cnpj}</td>
                        <td className="px-3 py-2">{c.name}</td>
                        <td className="px-3 py-2">
                          <Badge>Ativo</Badge>
                        </td>
                        <td className="px-3 py-2 flex gap-2">
                          <Button variant="ghost" className="min-h-8 px-2 text-xs" onClick={() => openEdit(c)}>
                            Editar
                          </Button>
                          <Button
                            variant="ghost"
                            className="min-h-8 px-2 text-xs"
                            onClick={() => {
                              setConfirmError(null)
                              setConfirmId(c.id)
                            }}
                          >
                            Desativar
                          </Button>
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
        title={editing ? 'Editar CNPJ' : 'Novo CNPJ'}
        footer={
          <>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>
              Descartar alterações
            </Button>
            <Button variant="primary" type="submit" form="cnpj-form" disabled={create.isPending || update.isPending}>
              Salvar CNPJ
            </Button>
          </>
        }
      >
        <form id="cnpj-form" onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-3">
          {formError ? <ErrorBanner message={formError} /> : null}
          <Input label="CNPJ" required value={cnpj} onChange={(e) => setCnpj(e.target.value)} />
          <Input label="Nome" required value={name} onChange={(e) => setName(e.target.value)} />
          {editing ? <CnpjContactLinksSection cnpjId={editing.id} /> : null}
        </form>
      </Dialog>
      <ConfirmDialog
        open={confirmId != null}
        title="Desativar CNPJ"
        message={
          confirmError ??
          'O CNPJ será marcado como inativo. Vínculos com contatos serão desativados; contatos compartilhados permanecem.'
        }
        confirmLabel="Desativar CNPJ"
        loading={deactivate.isPending}
        onConfirm={() => {
          if (confirmId == null) return
          void (async () => {
            setConfirmError(null)
            try {
              await deactivate.mutateAsync(confirmId)
              setSuccessMsg('CNPJ desativado.')
              setConfirmId(null)
            } catch {
              setConfirmError('Não foi possível desativar o CNPJ. Tente novamente.')
            }
          })()
        }}
        onClose={() => {
          setConfirmId(null)
          setConfirmError(null)
        }}
      />
    </>
  )
}
