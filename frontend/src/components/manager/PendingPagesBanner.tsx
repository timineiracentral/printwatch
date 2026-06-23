import { Link } from 'react-router-dom'

export interface PendingPagesBannerProps {
  pendingPct: number
  pendingCount: number
}

export function PendingPagesBanner({
  pendingPct,
  pendingCount,
}: PendingPagesBannerProps) {
  if (pendingCount === 0) {
    return null
  }

  return (
    <div
      role="status"
      className="rounded-lg border border-[#F5D90A] bg-[#FFF8E6] px-4 py-3"
    >
      <p className="text-sm text-[var(--text-primary)]">
        {pendingPct.toFixed(1)}% das páginas ({pendingCount}) estão sem classificação
        de cor no período.{' '}
        <Link to="/" className="font-medium text-[var(--accent)] underline">
          Revisar na auditoria de jobs
        </Link>
      </p>
    </div>
  )
}
