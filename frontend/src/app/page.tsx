'use client'

import { useEffect, useRef } from 'react'
import { motion, useAnimation } from 'motion/react'
import Navbar from '@/components/Navbar'
import WorldMapDemo from '@/components/world-map-demo'

export default function HomePage() {
  const contentRef = useRef<HTMLDivElement>(null)
  const contentControls = useAnimation()

  useEffect(() => {
    contentControls.start({
      opacity: [0, 1],
      y: [16, 0],
      transition: { duration: 0.6, ease: 'easeOut', delay: 0.15 },
    })
  }, [contentControls])

  return (
    <div className="relative bg-black min-h-screen overflow-hidden">
      <Navbar />
      <motion.div
        ref={contentRef}
        initial={{ opacity: 0, y: 16 }}
        animate={contentControls}
        className="relative z-10"
      >
        <WorldMapDemo />
      </motion.div>
    </div>
  )
}
