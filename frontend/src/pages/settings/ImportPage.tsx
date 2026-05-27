import { useState } from 'react'
import { PageHeader } from '../../components/layout/PageHeader'
import { triggerTemplateDownload } from '../../api/settings/import'
import { Button } from '../../components/ui/Button'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import { useImportCsv } from '../../hooks/useImport'
import type { ImportEntity, ImportResult } from '../../types/api'

const ENTITIES: {
  entity: ImportEntity
  title: string
  description: string
  filename: string
}[] = [
  {
    entity: 'departments',
    title: 'Departamentos',
    description: 'Código e nome; centro de custo opcional.',
    filename: 'departments.csv',
  },
  {
    entity: 'cost-centers',
    title: 'Centros de custo',
    description: 'Código e nome únicos.',
    filename: 'cost_centers.csv',
  },
  {
    entity: 'users',
    title: 'Usuários',
    description: 'Usuário CUPS, nome e departamento.',
    filename: 'users.csv',
  },
  {
    entity: 'printers',
    title: 'Impressoras',
    description: 'Nome de exibição e fila CUPS.',
    filename: 'printers.csv',
  },
]

function ImportCard({
  entity,
  title,
  description,
  filename,
  onResult,
}: (typeof ENTITIES)[number] & { onResult: (r: ImportResult) => void }) {
  const importMutation = useImportCsv()
  const [file, setFile] = useState<File | null>(null)
  const [strict, setStrict] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <article className="flex flex-col gap-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5">
      <div>
        <h2 className="text-[17px] font-semibold text-[var(--text-primary)]">{title}</h2>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{description}</p>
      </div>
      <Button
        variant="secondary"
        onClick={() => {
          void triggerTemplateDownload(entity, filename).catch(() =>
            setError('Falha ao baixar modelo.'),
          )
        }}
      >
        Baixar modelo
      </Button>
      <input
        type="file"
        accept=".csv,text/csv"
        className="text-sm text-[var(--text-secondary)]"
        aria-label={`Arquivo CSV para ${title}`}
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
      />
      <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
        <input
          type="checkbox"
          checked={strict}
          onChange={(e) => setStrict(e.target.checked)}
        />
        Modo estrito (rollback se houver erro)
      </label>
      {error ? <ErrorBanner message={error} /> : null}
      <Button
        variant="primary"
        disabled={!file || importMutation.isPending}
        onClick={() => {
          if (!file) return
          setError(null)
          void importMutation
            .mutateAsync({ entity, file, strict })
            .then(onResult)
            .catch(() => setError('Falha na importação.'))
        }}
      >
        {importMutation.isPending ? 'Importando…' : 'Importar'}
      </Button>
    </article>
  )
}

export function ImportPage() {
  const [result, setResult] = useState<ImportResult | null>(null)
  const [resultLabel, setResultLabel] = useState<string | null>(null)

  return (
    <>
      <PageHeader title="Importar CSV" />
      <div className="grid gap-6 lg:grid-cols-2">
        {ENTITIES.map((cfg) => (
          <ImportCard
            key={cfg.entity}
            {...cfg}
            onResult={(r) => {
              setResult(r)
              setResultLabel(cfg.title)
            }}
          />
        ))}
      </div>
      {result ? (
        <section className="mt-8 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5">
          <h2 className="text-[17px] font-semibold text-[var(--text-primary)]">
            Resultado — {resultLabel}
          </h2>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-[var(--text-secondary)]">Total</dt>
              <dd className="font-semibold">{result.total}</dd>
            </div>
            <div>
              <dt className="text-[var(--text-secondary)]">Criados</dt>
              <dd className="font-semibold text-[var(--accent)]">{result.created}</dd>
            </div>
            <div>
              <dt className="text-[var(--text-secondary)]">Atualizados</dt>
              <dd className="font-semibold">{result.updated}</dd>
            </div>
            <div>
              <dt className="text-[var(--text-secondary)]">Ignorados</dt>
              <dd className="font-semibold">{result.skipped}</dd>
            </div>
          </dl>
          {result.errors.length > 0 ? (
            <details className="mt-4" open>
              <summary className="cursor-pointer text-sm font-medium text-[var(--text-primary)]">
                Erros ({result.errors.length})
              </summary>
              <ul className="mt-2 max-h-48 overflow-y-auto text-sm text-[var(--text-secondary)]">
                {result.errors.map((err) => (
                  <li key={`${err.line}-${err.message}`} className="border-b border-[var(--border-subtle)] py-1">
                    Linha {err.line}: {err.message}
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </section>
      ) : null}
    </>
  )
}
