import { Outlet } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'

export function SettingsLayout() {
  return (
    <AppShell header={null}>
      <Outlet />
    </AppShell>
  )
}
