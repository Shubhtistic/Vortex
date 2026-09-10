"use client"

import { useEffect, useRef } from "react"
import gsap from "gsap"
import WorldMap from "@/components/ui/world-map"

const dots = [
  {
    start: { lat: 40.7128, lng: -74.006, label: "New York" },
    end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
  },
  {
    start: { lat: 51.5074, lng: -0.1278, label: "London" },
    end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
  },
  {
    start: { lat: 35.6762, lng: 139.6503, label: "Tokyo" },
    end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
  },
  {
    start: { lat: -33.8688, lng: 151.2093, label: "Sydney" },
    end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
  },
  {
    start: { lat: 37.7749, lng: -122.4194, label: "San Francisco" },
    end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
  },
  {
    start: { lat: 25.2048, lng: 55.2708, label: "Dubai" },
    end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
  },
]

export default function Hero() {
  const containerRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power4.out" } })

      tl.fromTo(
        ".hero-title",
        { y: 50, opacity: 0 },
        { y: 0, opacity: 1, duration: 1.2 }
      )
        .fromTo(
          ".hero-subtitle",
          { y: 30, opacity: 0 },
          { y: 0, opacity: 1, duration: 1 },
          "-=0.8"
        )
        .fromTo(
          ".hero-map",
          { opacity: 0, scale: 1.05 },
          { opacity: 1, scale: 1, duration: 1.4, ease: "power3.out" },
          "-=0.6"
        )
    }, containerRef)

    return () => ctx.revert()
  }, [])

  return (
    <section
      ref={containerRef}
      style={{ width: "100%", height: "100vh", position: "relative" }}
      className="bg-black overflow-hidden"
    >
      <div className="absolute inset-0 flex flex-col items-center justify-center z-10 pointer-events-none">
        <h1 className="hero-title text-6xl font-bold font-syne text-white">Vortex</h1>
        <p className="hero-subtitle text-xl mt-4 font-dm text-white/60">Next-gen event tracking</p>
      </div>
      <div className="hero-map absolute inset-0 -z-10 flex items-center justify-center px-4">
        <WorldMap dots={dots} lineColor="#06B6D4" dotColor="#06B6D4" endDotColor="#3DD9A4" />
      </div>
    </section>
  )
}
