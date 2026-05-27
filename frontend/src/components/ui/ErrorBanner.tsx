import { AlertCircle } from 'lucide-react'
import { Button } from './Button'

export interface ErrorBannerProps {
  message?: string
  onRetry?: () => void
}

export function ErrorBanner({
  message = 'Não foi possível carregar os dados.',
  onRetry,
}: ErrorBannerProps) {
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center gap-3 rounded-lg border border-[#ffc9c7] bg-[#fff5f5] px-4 py-3 text-sm text-[var(--destructive)]"
    >
      <AlertCircle className="size-5 shrink-0" aria-hidden />
      <p className="flex-1 text-[var(--text-primary)]">{message}</p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry} className="shrink-0">
          Tentar novamente
        </Button>
      ) : null}
    </div>
  )
}
