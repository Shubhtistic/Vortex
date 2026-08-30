import type { EventDay } from '../types'

interface EventsPerDayChartProps {
  data: EventDay[]
}

function EventsPerDayChart({ data }: EventsPerDayChartProps) {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-8">No data available</p>
  }

  const maxCount = Math.max(...data.map((d) => d.count), 1)

  return (
    <div className="flex items-end gap-1 h-48">
      {data.map((day) => (
        <div key={day.date} className="flex-1 flex flex-col items-center gap-1">
          <div
            className="w-full bg-blue-500 rounded-t"
            style={{ height: `${(day.count / maxCount) * 100}%` }}
          />
          <span className="text-xs text-gray-400 rotate-45 origin-left">
            {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
        </div>
      ))}
    </div>
  )
}

export default EventsPerDayChart
