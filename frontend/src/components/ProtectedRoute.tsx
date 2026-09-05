"use client"

import { usePathname, useRouter } from "next/navigation"
import { useEffect } from "react"
import { useAuth } from "@/lib/auth-context"

const PUBLIC_PATHS = ["/", "/login", "/signup"]

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (loading) return
    if (!isAuthenticated && !PUBLIC_PATHS.includes(pathname)) {
      router.push("/login")
    }
  }, [isAuthenticated, loading, pathname, router])

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <span className="font-dm text-white/60 text-sm tracking-widest uppercase">Loading...</span>
      </div>
    )
  }

  if (!isAuthenticated && !PUBLIC_PATHS.includes(pathname)) {
    return null
  }

  return <>{children}</>
}
