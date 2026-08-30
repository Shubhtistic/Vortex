import { createBrowserRouter } from 'react-router-dom'
import DashboardLayout from '@app/layout/DashboardLayout'
import RootLayout from '@app/layout/RootLayout'
import LoginPage from '@features/auth/pages/LoginPage'
import BootstrapPage from '@features/auth/pages/BootstrapPage'
import DashboardPage from '@features/dashboard/pages/DashboardPage'
import TeamMembersPage from '@features/users/pages/TeamMembersPage'
import TenantSettingsPage from '@features/tenants/pages/TenantSettingsPage'

const router = createBrowserRouter([
  {
    path: '/bootstrap',
    element: <BootstrapPage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        path: '',
        element: <DashboardLayout />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'team', element: <TeamMembersPage /> },
          { path: 'settings', element: <TenantSettingsPage /> },
        ],
      },
    ],
  },
])

export default router
