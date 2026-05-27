import { Button } from '../ui/Button'

export interface UnmappedQueuesBannerProps {
  queues: string[]
  onRegisterQueue: (cupsQueueName: string) => void
}

export function UnmappedQueuesBanner({
  queues,
  onRegisterQueue,
}: UnmappedQueuesBannerProps) {
  if (queues.length === 0) return null

  const n = queues.length
  const label =
    n === 1
      ? '1 fila no log ainda não cadastrada'
      : `${n} filas no log ainda não cadastradas`

  return (
    <div
      role="status"
      className="mb-6 rounded-lg border border-[#F5D90A] bg-[#FFF8E6] px-4 py-3"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-[var(--text-primary)]">{label}</p>
          <details className="mt-2">
            <summary className="cursor-pointer text-sm text-[var(--accent)]">
              Ver filas
            </summary>
            <ul className="mt-2 list-inside list-disc text-sm text-[var(--text-secondary)]">
              {queues.map((q) => (
                <li key={q}>{q}</li>
              ))}
            </ul>
          </details>
        </div>
        <Button
          variant="secondary"
          onClick={() => onRegisterQueue(queues[0] ?? '')}
        >
          Cadastrar fila
        </Button>
      </div>
    </div>
  )
}
