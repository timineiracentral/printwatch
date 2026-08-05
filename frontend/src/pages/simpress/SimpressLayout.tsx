import { Navigate, Outlet } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { useSimpressHealth } from '../../hooks/useSimpressHealth'

export function SimpressLayout() {
  const { data: simpressEnabled, isLoading, isError } = useSimpressHealth()

  if (!isLoading && (isError || !simpressEnabled)) {
    return <Navigate to="/" replace />
  }

  return (
    <AppShell header={null}>
      <Outlet />
    </AppShell>
  )
}
