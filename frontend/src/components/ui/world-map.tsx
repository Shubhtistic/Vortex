"use client"

import * as turf from "@turf/turf"
import DottedMap from "dotted-map"
import { motion } from "motion/react"
import Image from "next/image"
import { useMemo, useRef } from "react"

interface Point {
  lat: number
  lng: number
  label?: string
}

interface MapProps {
  dots?: Array<{
    start: Point
    end: Point
  }>
  lineColor?: string
  dotColor?: string
  endDotColor?: string
}

const ZOOM = 0.55
const ARC_CURVE = 40 * ZOOM

// Simplified land polygons (major continents in lat/lng)
const LAND_POLYGONS = [
  // North America
  {
    type: "Feature",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [-170, 70],
          [-140, 72],
          [-100, 72],
          [-60, 65],
          [-55, 47],
          [-67, 44],
          [-80, 30],
          [-100, 25],
          [-115, 32],
          [-125, 42],
          [-130, 55],
          [-165, 65],
          [-170, 70],
        ],
      ],
    },
  },
  // South America
  {
    type: "Feature",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [-80, 10],
          [-60, 12],
          [-35, -5],
          [-35, -20],
          [-50, -30],
          [-55, -35],
          [-70, -55],
          [-75, -45],
          [-70, -20],
          [-80, 0],
          [-80, 10],
        ],
      ],
    },
  },
  // Europe
  {
    type: "Feature",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [-10, 60],
          [0, 65],
          [10, 62],
          [25, 70],
          [40, 68],
          [50, 55],
          [30, 45],
          [10, 38],
          [-5, 36],
          [-10, 45],
          [-10, 60],
        ],
      ],
    },
  },
  // Africa
  {
    type: "Feature",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [-15, 35],
          [10, 35],
          [30, 32],
          [50, 12],
          [50, -2],
          [40, -15],
          [35, -35],
          [20, -35],
          [15, -5],
          [0, 5],
          [-15, 10],
          [-17, 25],
          [-15, 35],
        ],
      ],
    },
  },
  // Asia
  {
    type: "Feature",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [30, 70],
          [60, 72],
          [100, 70],
          [140, 60],
          [150, 50],
          [140, 35],
          [120, 20],
          [100, 10],
          [80, 10],
          [70, 25],
          [50, 35],
          [30, 45],
          [30, 70],
        ],
      ],
    },
  },
  // Australia
  {
    type: "Feature",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [115, -15],
          [145, -12],
          [155, -25],
          [150, -38],
          [135, -38],
          [115, -30],
          [115, -15],
        ],
      ],
    },
  },
]

// Combine all land polygons into one MultiPolygon
const ALL_LAND = turf.multiPolygon(LAND_POLYGONS.map((p: any) => p.geometry.coordinates))

const projectPoint = (lat: number, lng: number) => {
  const baseX = (lng + 180) * (800 / 360)
  const baseY = (90 - lat) * (400 / 180)
  return {
    x: baseX * ZOOM + 400 * (1 - ZOOM),
    y: baseY * ZOOM + 200 * (1 - ZOOM),
  }
}

// Find nearest point on land using raster-like approach
const findLandPoint = (
  lat: number,
  lng: number,
  maxIter: number = 20
): { lat: number; lng: number } => {
  let currentLat = lat
  let currentLng = lng
  let step = 2 // degrees

  for (let i = 0; i < maxIter; i++) {
    const point = turf.point([currentLng, currentLat])
    if (turf.booleanPointInPolygon(point as any, ALL_LAND as any)) {
      return { lat: currentLat, lng: currentLng }
    }
    // Move towards nearest land (try all directions)
    let bestPoint = null
    let bestDist = Infinity
    for (const [dLat, dLng] of [
      [-step, 0],
      [step, 0],
      [0, -step],
      [0, step],
    ]) {
      const candidate = turf.point([currentLng + dLng, currentLat + dLat])
      if (turf.booleanPointInPolygon(candidate as any, ALL_LAND as any)) {
        const dist = Math.sqrt(dLat * dLat + dLng * dLng)
        if (dist < bestDist) {
          bestDist = dist
          bestPoint = { lat: currentLat + dLat, lng: currentLng + dLng }
        }
      }
    }
    if (bestPoint) {
      currentLat = bestPoint.lat
      currentLng = bestPoint.lng
    } else {
      step *= 0.8
      if (step < 0.1) break
    }
  }
  return { lat: currentLat, lng: currentLng }
}

export default function WorldMap({
  dots = [],
  lineColor = "#9B1313",
  dotColor,
  endDotColor,
}: MapProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const map = new DottedMap({ height: 100, grid: "diagonal" })

  const svgMap = map.getSVG({
    radius: 0.22,
    color: "#FFFFFF40",
    shape: "circle",
    backgroundColor: "black",
  })

  // Fix dots to ensure they're on land (computed synchronously)
  const landDots = useMemo(() => {
    return dots.map((dot) => ({
      ...dot,
      start: findLandPoint(dot.start.lat, dot.start.lng),
      end: findLandPoint(dot.end.lat, dot.end.lng),
    }))
  }, [dots])

  const createCurvedPath = (start: { x: number; y: number }, end: { x: number; y: number }) => {
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

        {/* Arc paths */}
        {landDots.map((dot, i) => {
          const s = projectPoint(dot.start.lat, dot.start.lng)
          const e = projectPoint(dot.end.lat, dot.end.lng)
          const path = createCurvedPath(s, e)
          return (
            <motion.path
              key={`arc-${i}`}
              d={path}
              fill="none"
              stroke={lineColor}
              strokeWidth="1.6"
              strokeLinecap="round"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{
                duration: 1.0,
                delay: 1.0 + i * 0.2,
                ease: "easeInOut",
              }}
            />
          )
        })}

        {/* Start points */}
        {landDots.map((dot, i) => {
          const s = projectPoint(dot.start.lat, dot.start.lng)
          return (
            <g key={`start-${i}`} style={{ animation: `fadeIn 0.4s ease ${0.4 + i * 0.08}s both` }}>
              <circle cx={s.x} cy={s.y} r="3" fill={dotColor || lineColor} />
              <circle cx={s.x} cy={s.y} r="3" fill={dotColor || lineColor} opacity="0.5">
                <animate
                  attributeName="r"
                  from="3"
                  to="10"
                  dur="1.5s"
                  begin={`${0.4 + i * 0.08}s`}
                  repeatCount="indefinite"
                />
                <animate
                  attributeName="opacity"
                  from="0.5"
                  to="0"
                  dur="1.5s"
                  begin={`${0.4 + i * 0.08}s`}
                  repeatCount="indefinite"
                />
              </circle>
            </g>
          )
        })}

        {/* End points */}
        {landDots.map((dot, i) => {
          const e = projectPoint(dot.end.lat, dot.end.lng)
          return (
            <g key={`end-${i}`} style={{ animation: `fadeIn 0.4s ease ${1.8 + i * 0.2}s both` }}>
              <circle cx={e.x} cy={e.y} r="3" fill={endDotColor || "#E35336"} />
              <circle cx={e.x} cy={e.y} r="5" fill={endDotColor || "#FDFBD4"} opacity="0.13">
                <animate
                  attributeName="r"
                  from="3"
                  to="10"
                  dur="1.5s"
                  begin={`${1.8 + i * 0.2}s`}
                  repeatCount="indefinite"
                />
                <animate
                  attributeName="opacity"
                  from="0.5"
                  to="0"
                  dur="1.5s"
                  begin={`${1.8 + i * 0.2}s`}
                  repeatCount="indefinite"
                />
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
