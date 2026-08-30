import type { TopUrl } from '../types'

interface TopUrlsTableProps {
  urls: TopUrl[]
}

function TopUrlsTable({ urls }: TopUrlsTableProps) {
  if (urls.length === 0) {
    return <p className="text-gray-500 text-center py-8">No data available</p>
  }

  return (
    <div className="space-y-2">
      {urls.map((url, index) => (
        <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
          <span className="text-sm text-gray-600 truncate max-w-[200px]" title={url.url}>
            {url.url}
          </span>
          <span className="text-sm font-medium text-gray-800">{url.clicks.toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}

export default TopUrlsTable
