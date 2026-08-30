import { useDashboardStats, useEventsPerDay, useTopUrls } from '../hooks'
import StatsCard from '../components/StatsCard'
import EventsPerDayChart from '../components/EventsPerDayChart'
import TopUrlsTable from '../components/TopUrlsTable'

function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
  const { data: events, isLoading: eventsLoading } = useEventsPerDay(7)
  const { data: topUrls, isLoading: urlsLoading } = useTopUrls(10)

  if (statsLoading || eventsLoading || urlsLoading) {
    return <div className="p-6">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Events"
          value={stats?.total_events ?? 0}
          change="+12%"
        />
        <StatsCard
          title="Total Links"
          value={stats?.total_links ?? 0}
          change="+5%"
        />
        <StatsCard
          title="Total Clicks"
          value={stats?.total_clicks ?? 0}
          change="+18%"
        />
        <StatsCard
          title="Events Today"
          value={stats?.events_today ?? 0}
          change="+8%"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Events Over Time</h3>
          <EventsPerDayChart data={events ?? []} />
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Top URLs</h3>
          <TopUrlsTable urls={topUrls ?? []} />
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
