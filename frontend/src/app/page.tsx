"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"
import Navbar from "@/components/Navbar"
import WorldMapDemo from "@/components/world-map-demo"
import { useAuth } from "@/lib/auth-context"

export default function HomePage() {
  const router = useRouter()
  const { isAuthenticated, loading } = useAuth()

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.replace("/dashboard")
    }
  }, [isAuthenticated, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <span className="font-dm text-white/60 text-sm tracking-widest uppercase">Loading...</span>
      </div>
    )
  }

  return (
    <div className="relative bg-black min-h-screen">
      <Navbar />
      <WorldMapDemo />
    </div>
  )
}
