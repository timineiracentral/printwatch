import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchPrinterUsers } from '../../api/settings/users'
import { ErrorBanner } from '../ui/ErrorBanner'
import { Skeleton } from '../ui/Skeleton'

export function PrinterUsersPanel({ printerId }: { printerId: number }) {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['printers', printerId, 'users'],
    queryFn: () => fetchPrinterUsers(printerId),
  })

  if (isError) {
    return (
      <ErrorBanner
        message="Não foi possível carregar usuários com acesso."
        onRetry={() => void refetch()}
      />
    )
  }

  if (isLoading) return <Skeleton className="h-16 w-full" />

  const users = data ?? []
  return (
    <div className="mt-4 border-t border-[var(--border-subtle)] pt-4">
      <h3 className="mb-1 text-sm font-semibold">Usuários com acesso</h3>
      <p className="mb-2 text-xs text-[var(--text-secondary)]">
        Somente leitura — edite na{' '}
        <Link to="/settings/users" className="text-[var(--accent)] underline">
          ficha do usuário
        </Link>
        .
      </p>
      {users.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]">Nenhum usuário atribuído.</p>
      ) : (
        <ul className="space-y-1 text-sm">
          {users.map((u) => (
            <li key={u.id}>
              {u.display_name}
              {u.is_default ? (
                <span className="ml-2 text-xs text-[var(--accent)]">(padrão)</span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
