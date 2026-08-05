import { Contact } from 'lucide-react'
import { useMemo, useState } from 'react'
import { ContactCnpjLinksSection } from '../../components/simpress/ContactCnpjLinksSection'
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
import { useSimpressContacts } from '../../hooks/useSimpressContacts'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { isValidPhone, normalizePhone } from '../../lib/simpressPhone'
import type { ContactCreate, ContactRead, ContactUpdate } from '../../types/api'

const PHONE_HELPER =
  'DDI + DDD + número. Salvar grava só dígitos (ex.: 5531999999999).'
const PHONE_INVALID_MSG =
  'Informe um telefone com DDI e DDD (somente dígitos após salvar). Ex.: 5531999999999'

export function ContatosPage() {
  const { list, create, update, deactivate } = useSimpressContacts(false)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<ContactRead | null>(null)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
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
        c.name.toLowerCase().includes(q) ||
        c.phone.includes(q.replace(/\D/g, '')),
    )
  }, [list.data, debouncedSearch])

  function openCreate() {
    setEditing(null)
    setName('')
    setPhone('55')
    setFormError(null)
    setDialogOpen(true)
  }

  function openEdit(c: ContactRead) {
    setEditing(c)
    setName(c.name)
    setPhone(c.phone)
    setFormError(null)
    setDialogOpen(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const digits = normalizePhone(phone)
    if (!isValidPhone(digits)) {
      setFormError(PHONE_INVALID_MSG)
      return
    }
    const trimmedName = name.trim()
    if (!trimmedName) {
      setFormError('Não foi possível salvar. Verifique os campos e tente novamente.')
      return
    }
    const payload: ContactCreate = { name: trimmedName, phone: digits }
    try {
      if (editing) {
        await update.mutateAsync({ id: editing.id, body: payload as ContactUpdate })
        setSuccessMsg('Contato atualizado.')
      } else {
        await create.mutateAsync(payload)
        setSuccessMsg('Contato cadastrado.')
      }
      setDialogOpen(false)
    } catch {
      setFormError('Não foi possível salvar. Verifique os campos e tente novamente.')
    }
  }

  return (
    <>
      <PageHeader
        title="Contatos"
        actions={
          <Button variant="primary" onClick={openCreate}>
            Novo contato
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
        <ErrorBanner message="Erro ao carregar contatos." onRetry={() => void list.refetch()} />
      ) : (
        <div className="overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-subtle)]">
                {['Nome', 'Telefone', 'Status', 'Ações'].map((h) => (
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
                            icon={<Contact className="mx-auto size-10" />}
                            heading="Nenhum contato"
                            body="Cadastre o primeiro contato WhatsApp. CNPJs podem ser vinculados depois."
                            actionLabel="Cadastrar primeiro contato"
                            onAction={openCreate}
                          />
                        </td>
                      </tr>
                    )
                  : filtered.map((c, idx) => (
                      <tr key={c.id} className={idx % 2 === 1 ? 'bg-[var(--bg-muted)]/40' : ''}>
                        <td className="px-3 py-2">{c.name}</td>
                        <td className="px-3 py-2 font-mono text-xs">{c.phone}</td>
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
        title={editing ? 'Editar contato' : 'Novo contato'}
        footer={
          <>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>
              Descartar alterações
            </Button>
            <Button variant="primary" type="submit" form="contato-form" disabled={create.isPending || update.isPending}>
              Salvar contato
            </Button>
          </>
        }
      >
        <form id="contato-form" onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-3">
          {formError ? <ErrorBanner message={formError} /> : null}
          <Input label="Nome" required value={name} onChange={(e) => setName(e.target.value)} />
          <div className="flex flex-col gap-1">
            <Input label="Telefone" required value={phone} onChange={(e) => setPhone(e.target.value)} />
            <p className="text-xs text-[var(--text-secondary)]">{PHONE_HELPER}</p>
          </div>
          {editing ? <ContactCnpjLinksSection contactId={editing.id} /> : null}
        </form>
      </Dialog>
      <ConfirmDialog
        open={confirmId != null}
        title="Desativar contato"
        message={
          confirmError ??
          'O contato será marcado como inativo e deixará de aparecer nas listas.'
        }
        confirmLabel="Desativar contato"
        loading={deactivate.isPending}
        onConfirm={() => {
          if (confirmId == null) return
          void (async () => {
            setConfirmError(null)
            try {
              await deactivate.mutateAsync(confirmId)
              setSuccessMsg('Contato desativado.')
              setConfirmId(null)
            } catch {
              setConfirmError('Não foi possível desativar o contato. Tente novamente.')
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
