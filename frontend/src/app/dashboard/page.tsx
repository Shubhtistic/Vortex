"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { getAccessToken } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"

function decodeJwtPayload(token: string): { user_id: string; org_id: string; role: string } | null {
  try {
    const payload = token.split(".")[1]
    if (!payload) return null
    const decoded = JSON.parse(atob(payload)) as {
      user_id?: string
      org_id?: string
      role?: string
    }
    if (!decoded.user_id || !decoded.org_id || !decoded.role) return null
    return { user_id: decoded.user_id, org_id: decoded.org_id, role: decoded.role }
  } catch {
    return null
  }
}

export default function DashboardPage() {
  const router = useRouter()
  const { logout, isAuthenticated } = useAuth()
  const [claims, setClaims] = useState<{ user_id: string; org_id: string; role: string } | null>(
    null
  )
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login")
      return
    }
    const token = getAccessToken()
    if (token) {
      setClaims(decodeJwtPayload(token))
    }
    setLoading(false)
  }, [isAuthenticated, router])

  const handleLogout = async () => {
    await logout()
    router.replace("/login")
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <span className="font-dm text-white/60 text-sm tracking-widest uppercase">Loading...</span>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black">
      <nav className="fixed top-0 left-0 right-0 z-50">
        <div className="mx-auto max-w-5xl px-8 mt-4 bg-white/5 backdrop-blur-3xl rounded-full">
          <div className="flex justify-between items-center py-4">
            <Link href="/" className="text-white text-xl font-bold font-syne tracking-tight">
              Vortex
            </Link>
            <div className="flex items-center gap-4">
              <span className="text-white/50 text-sm font-dm">
                {claims?.role && (
                  <span className="px-2 py-0.5 rounded-full bg-white/10 text-xs uppercase tracking-wider">
                    {claims.role}
                  </span>
                )}
              </span>
              <button
                type="button"
                onClick={handleLogout}
                className="text-white/60 hover:text-white transition-colors text-sm font-dm"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="pt-24 px-4 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="font-syne text-4xl font-bold text-white mb-4">Dashboard</h1>
          <p className="text-white/40 font-dm text-sm">
            Organization: <span className="text-white/60">{claims?.org_id}</span>
          </p>
          <p className="text-white/40 font-dm text-sm mt-1">
            User: <span className="text-white/60">{claims?.user_id}</span>
          </p>
        </div>
      </div>
    </div>
  )
}
