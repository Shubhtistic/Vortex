"use client"

interface TrendRow {
  bucket: string
  value: number
}

interface AnalyticsTrendChartProps {
  rows: TrendRow[]
  color?: string
  valueLabel: string
}

function formatBucket(value: string, includeTime: boolean) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    ...(includeTime ? { hour: "numeric" } : {}),
    timeZone: "UTC",
  }).format(date)
}

export default function AnalyticsTrendChart({
  rows,
  color = "#06b6d4",
  valueLabel,
}: AnalyticsTrendChartProps) {
  if (rows.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center rounded-lg border border-dashed border-white/10 text-center">
        <div>
          <p className="font-syne text-sm text-white/60">No activity in this period</p>
          <p className="mt-1 font-dm text-xs text-white/35">
            Try a wider date range or change the filters.
          </p>
        </div>
      </div>
    )
  }

  const width = 1000
  const top = 18
  const bottom = 188
  const inset = 28
  const max = Math.max(...rows.map((row) => row.value), 1)
  const points = rows.map((row, index) => {
    const x =
      rows.length === 1 ? width / 2 : inset + (index / (rows.length - 1)) * (width - inset * 2)
    const y = bottom - (row.value / max) * (bottom - top)
    return { ...row, x, y }
  })
  const line = points.map((point) => `${point.x},${point.y}`).join(" ")
  const area = `${points[0].x},${bottom} ${line} ${points[points.length - 1].x},${bottom}`
  const labelIndices = [...new Set([0, Math.floor((rows.length - 1) / 2), rows.length - 1])]

  return (
    <div>
      <div className="mb-2 flex items-center justify-between font-dm text-[11px] text-white/35">
        <span>0</span>
        <span>
          {max.toLocaleString()} {valueLabel}
        </span>
      </div>
      <svg
        viewBox={`0 0 ${width} 220`}
        className="h-52 w-full overflow-visible sm:h-60"
        role="img"
        aria-label={`${valueLabel} over time`}
        preserveAspectRatio="none"
      >
        <title>{`${valueLabel} over time`}</title>
        {[0, 1, 2, 3].map((lineIndex) => {
          const y = top + (lineIndex / 3) * (bottom - top)
          return (
            <line
              key={lineIndex}
              x1={inset}
              x2={width - inset}
              y1={y}
              y2={y}
              stroke="rgba(255,255,255,0.08)"
              strokeDasharray="4 8"
            />
          )
        })}
        <polygon points={area} fill={color} opacity="0.12" />
        <polyline
          points={line}
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />
        {points
          .filter((_, index) => rows.length < 24 || index % Math.ceil(rows.length / 12) === 0)
          .map((point) => (
            <circle key={point.bucket} cx={point.x} cy={point.y} r="4" fill={color}>
              <title>{`${formatBucket(point.bucket, true)}: ${point.value.toLocaleString()} ${valueLabel}`}</title>
            </circle>
          ))}
      </svg>
      <div className="-mt-1 flex justify-between px-2 font-dm text-[10px] text-white/35 sm:text-xs">
        {labelIndices.map((index) => (
          <span key={rows[index].bucket}>{formatBucket(rows[index].bucket, false)}</span>
        ))}
      </div>
    </div>
  )
}
