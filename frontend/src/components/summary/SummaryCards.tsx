import { Link } from 'react-router-dom'
import { useStatsSummary } from '../../hooks/useStatsSummary'
import { formatNumberPtBr, formatTopLabel } from '../../lib/format'
import type { TopEntry } from '../../types/api'
import { ErrorBanner } from '../ui/ErrorBanner'
import { Skeleton } from '../ui/Skeleton'
import { SummaryCard } from './SummaryCard'

const ERROR_MESSAGE =
  'Não foi possível carregar os dados. Verifique se o servidor está online e tente novamente.'

function SummaryCardSkeleton() {
  return (
    <div
      className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-4 shadow-[0_1px_2px_rgba(0,0,0,0.04)]"
      aria-hidden
    >
      <Skeleton className="mb-3 h-5 w-28" />
      <Skeleton className="h-8 w-24" />
    </div>
  )
}

function topCardValue(entry: TopEntry | undefined): { value?: string; isEmpty: boolean } {
  if (!entry) {
    return { isEmpty: true }
  }
  return { value: formatTopLabel(entry.name, entry.pages), isEmpty: false }
}

export function SummaryCards() {
  const { data, isLoading, isError, refetch } = useStatsSummary()

  if (isLoading) {
    return (
      <div
        className="grid grid-cols-2 gap-4 xl:grid-cols-4"
        aria-busy="true"
        aria-label="Carregando resumo"
      >
        {Array.from({ length: 4 }, (_, i) => (
          <SummaryCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorBanner
        message={ERROR_MESSAGE}
        onRetry={() => {
          void refetch()
        }}
      />
    )
  }

  const topUser = topCardValue(data?.mes.top_users[0])
  const topPrinter = topCardValue(data?.mes.top_printers[0])

  return (
    <>
    <p className="mb-2 text-sm text-[var(--text-secondary)]">
      Resumo rápido (hoje / mês).{' '}
      <Link to="/manager" className="font-medium text-[var(--accent)] underline">
        Abrir painel gerencial
      </Link>
    </p>
    <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
      <SummaryCard
        variant="metric"
        label="Jobs hoje"
        value={formatNumberPtBr(data?.hoje.jobs ?? 0)}
      />
      <SummaryCard
        variant="metric"
        label="Páginas hoje"
        value={formatNumberPtBr(data?.hoje.pages ?? 0)}
      />
      <SummaryCard
        variant="top"
        label="Top usuário do mês"
        value={topUser.value}
        isEmpty={topUser.isEmpty}
      />
      <SummaryCard
        variant="top"
        label="Top impressora do mês"
        value={topPrinter.value}
        isEmpty={topPrinter.isEmpty}
      />
    </div>
    </>
  )
}
