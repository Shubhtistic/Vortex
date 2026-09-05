'use client'

import { useRef } from 'react'
import { motion } from 'motion/react'
import Image from 'next/image'
import DottedMap from 'dotted-map'

interface MapProps {
  dots?: Array<{
    start: { lat: number; lng: number; label?: string }
    end: { lat: number; lng: number; label?: string }
  }>
  lineColor?: string
}

const ZOOM = 0.55
const ARC_CURVE = 40 * ZOOM

export default function WorldMap({
  dots = [],
  lineColor = '#0ea5e9',
}: MapProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const map = new DottedMap({ height: 100, grid: 'diagonal' })

  const svgMap = map.getSVG({
    radius: 0.22,
    color: '#FFFFFF40',
    shape: 'circle',
    backgroundColor: 'black',
  })

  const projectPoint = (lat: number, lng: number) => {
    const baseX = (lng + 180) * (800 / 360)
    const baseY = (90 - lat) * (400 / 180)
    return {
      x: baseX * ZOOM + 400 * (1 - ZOOM),
      y: baseY * ZOOM + 200 * (1 - ZOOM),
    }
  }

  const createCurvedPath = (
    start: { x: number; y: number },
    end: { x: number; y: number }
  ) => {
    const midX = (start.x + end.x) / 2
    const midY = Math.min(start.y, end.y) - ARC_CURVE
    return `M ${start.x} ${start.y} Q ${midX} ${midY} ${end.x} ${end.y}`
  }

  return (
    <div className="w-full aspect-[2/1] bg-black rounded-lg relative font-sans overflow-hidden">
      <Image
        src={`data:image/svg+xml;utf8,${encodeURIComponent(svgMap)}`}
        className="h-full w-full [mask-image:linear-gradient(to_bottom,transparent,white_10%,white_90%,transparent)] pointer-events-none select-none"
        alt="world map"
        height={495}
        width={1056}
        unoptimized
        draggable={false}
      />
      <svg
        ref={svgRef}
        viewBox="0 0 800 400"
        className="w-full h-full absolute inset-0 pointer-events-none select-none"
      >
        <defs>
          <linearGradient id="path-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="white" stopOpacity="0" />
            <stop offset="5%" stopColor={lineColor} stopOpacity="1" />
            <stop offset="95%" stopColor={lineColor} stopOpacity="1" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Arc paths — animate after map fades in */}
        {dots.map((dot, i) => {
          const s = projectPoint(dot.start.lat, dot.start.lng)
          const e = projectPoint(dot.end.lat, dot.end.lng)
          const path = createCurvedPath(s, e)
          return (
            <motion.path
              key={`arc-${i}`}
              d={path}
              fill="none"
              stroke={lineColor}
              strokeWidth="1.4"
              strokeLinecap="round"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{
                duration: 1.0,
                delay: 1.0 + i * 0.2,
                ease: 'easeInOut',
              }}
            />
          )
        })}

        {/* Start points — appear with map fade */}
        {dots.map((dot, i) => {
          const s = projectPoint(dot.start.lat, dot.start.lng)
          return (
            <g key={`start-${i}`} style={{ animation: `fadeIn 0.4s ease ${0.4 + i * 0.08}s both` }}>
              <circle cx={s.x} cy={s.y} r="2.5" fill={lineColor} />
              <circle cx={s.x} cy={s.y} r="2.5" fill={lineColor} opacity="0.5">
                <animate attributeName="r" from="2.5" to="9" dur="1.5s" begin={`${0.4 + i * 0.08}s`} repeatCount="indefinite" />
                <animate attributeName="opacity" from="0.5" to="0" dur="1.5s" begin={`${0.4 + i * 0.08}s`} repeatCount="indefinite" />
              </circle>
            </g>
          )
        })}

        {/* End points — appear after arcs complete */}
        {dots.map((dot, i) => {
          const e = projectPoint(dot.end.lat, dot.end.lng)
          return (
            <g key={`end-${i}`} style={{ animation: `fadeIn 0.4s ease ${1.8 + i * 0.2}s both` }}>
              <circle cx={e.x} cy={e.y} r="2.5" fill={lineColor} />
              <circle cx={e.x} cy={e.y} r="2.5" fill={lineColor} opacity="0.5">
                <animate attributeName="r" from="2.5" to="9" dur="1.5s" begin={`${1.8 + i * 0.2}s`} repeatCount="indefinite" />
                <animate attributeName="opacity" from="0.5" to="0" dur="1.5s" begin={`${1.8 + i * 0.2}s`} repeatCount="indefinite" />
              </circle>
            </g>
          )
        })}
      </svg>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  )
}
