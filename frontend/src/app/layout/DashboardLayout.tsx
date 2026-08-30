import { Outlet } from 'react-router-dom'
import Topbar from '@app/layout/Topbar'
import Sidebar from '@app/layout/Sidebar'

function DashboardLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Topbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout
