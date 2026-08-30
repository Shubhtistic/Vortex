interface StatsCardProps {
  title: string
  value: number
  change: string
}

function StatsCard({ title, value, change }: StatsCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-sm text-gray-500">{title}</p>
      <div className="flex items-end justify-between">
        <p className="text-2xl font-bold text-gray-800">{value.toLocaleString()}</p>
        <span className="text-sm text-green-600">{change}</span>
      </div>
    </div>
  )
}

export default StatsCard
