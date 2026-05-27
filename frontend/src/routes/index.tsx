import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { JobsPage } from '../pages/JobsPage'
import { SettingsLayout } from '../pages/settings/SettingsLayout'
import { SettingsPlaceholder } from '../pages/settings/SettingsPlaceholder'

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<JobsPage />} />
        <Route path="/settings" element={<SettingsLayout />}>
          <Route index element={<Navigate to="printers" replace />} />
          <Route
            path="printers"
            element={<SettingsPlaceholder title="Impressoras" />}
          />
          <Route
            path="departments"
            element={<SettingsPlaceholder title="Departamentos" />}
          />
          <Route
            path="cost-centers"
            element={<SettingsPlaceholder title="Centros de custo" />}
          />
          <Route
            path="users"
            element={<SettingsPlaceholder title="Usuários" />}
          />
          <Route
            path="import"
            element={<SettingsPlaceholder title="Importar CSV" />}
          />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
