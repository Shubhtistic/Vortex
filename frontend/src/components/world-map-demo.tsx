'use client'

import { useEffect, useRef } from 'react'
import { motion, useAnimation } from 'motion/react'
import WorldMap from '@/components/ui/world-map'

export default function WorldMapDemo() {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<HTMLDivElement>(null)

  const containerControls = useAnimation()
  const mapControls = useAnimation()

  useEffect(() => {
    const run = async () => {
      await containerControls.start({
        opacity: [0, 1],
        y: [20, 0],
        transition: { duration: 0.7, ease: 'easeOut' },
      })
      await mapControls.start({
        opacity: [0, 1],
        scale: [0.96, 1],
        transition: {
          duration: 0.9,
          ease: 'easeOut',
          delay: 0.2,
        },
      })
    }
    run()
  }, [containerControls, mapControls])

  return (
    <div ref={containerRef} className="relative w-full bg-black text-white overflow-hidden">
      {/* Top fade */}
      <div className="absolute top-0 left-0 right-0 h-40 pointer-events-none bg-gradient-to-b from-black via-black/90 to-transparent z-20" />
      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-40 pointer-events-none bg-gradient-to-t from-black via-black/90 to-transparent z-20" />

      <motion.div
        ref={mapRef}
        animate={mapControls}
        initial={{ opacity: 0, scale: 0.96 }}
        className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4 py-24"
      >
        <div className="w-full max-w-6xl">
          <WorldMap
            dots={[
              {
                start: { lat: 64.2008, lng: -149.4937 }, // Alaska (Fairbanks)
                end: { lat: 34.0522, lng: -118.2437 }, // Los Angeles
              },
              {
                start: { lat: 64.2008, lng: -149.4937 }, // Alaska (Fairbanks)
                end: { lat: -15.7975, lng: -47.8919 }, // Brazil (Brasília)
              },
              {
                start: { lat: -15.7975, lng: -47.8919 }, // Brazil (Brasília)
                end: { lat: 38.7223, lng: -9.1393 }, // Lisbon
              },
              {
                start: { lat: 51.5074, lng: -0.1278 }, // London
                end: { lat: 28.6139, lng: 77.209 }, // New Delhi
              },
              {
                start: { lat: 28.6139, lng: 77.209 }, // New Delhi
                end: { lat: 43.1332, lng: 131.9113 }, // Vladivostok
              },
              {
                start: { lat: 28.6139, lng: 77.209 }, // New Delhi
                end: { lat: -1.2921, lng: 36.8219 }, // Nairobi
              },
            ]}
          />
        </div>
      </motion.div>
    </div>
  )
}
