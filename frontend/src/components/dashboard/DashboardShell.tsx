"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import Dock from "@/components/dashboard/Dock"
import { useAuth } from "@/lib/auth-context"

interface NavItem {
  href: string
  label: string
  icon: React.ReactNode
}

interface DashboardShellProps {
  children: React.ReactNode
  title?: string
  subtitle?: string
  showDock?: boolean
}

const navItems: NavItem[] = [
  {
    href: "/dashboard",
    label: "Overview",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
        />
      </svg>
    ),
  },
  {
    href: "/dashboard/members",
    label: "Members",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
        />
      </svg>
    ),
  },
  {
    href: "/dashboard/tenants",
    label: "Tenants",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
        />
      </svg>
    ),
  },
  {
    href: "/dashboard/settings",
    label: "Settings",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826 3.31 2.37 2.37.996.608 2.296.07 2.572-1.065z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
    ),
  },
]

export default function DashboardShell({
  children,
  title,
  subtitle,
  showDock = true,
}: DashboardShellProps) {
  const { user, logout } = useAuth()
  const pathname = usePathname()
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50)
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const handleLogout = async () => {
    await logout()
    window.location.href = "/login"
  }

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`)

  return (
    <div className="min-h-screen bg-black relative">
      {/* Top nav — matches landing page navbar behavior: transparent at top, glass pill on scroll */}
      <nav className="fixed top-0 left-0 right-0 z-50">
        <div
          className={`mx-auto w-full transition-all duration-300 max-w-[1800px] px-4 sm:px-6 xl:px-10 2xl:px-12 ${
            isScrolled ? "bg-white/5 backdrop-blur-[24px] rounded-full mt-6" : "bg-transparent mt-2"
          }`}
        >
          <div className="flex justify-between items-center py-4">
            <Link href="/" className="text-white text-xl font-bold font-syne tracking-tight">
              Vortex
            </Link>
            <div className="flex items-center gap-6">
              {user && (
                <div className="flex items-center gap-3">
                  <div className="text-right hidden sm:block">
                    <p className="text-sm text-white font-dm">
                      {user.first_name} {user.last_name}
                    </p>
                    <p className="text-xs text-white/40 font-dm">{user.email}</p>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-brand/20 border border-brand/30 flex items-center justify-center">
                    <span className="text-xs font-syne font-bold text-brand">
                      {user.first_name?.[0]}
                      {user.last_name?.[0]}
                    </span>
                  </div>
                </div>
              )}
              <button
                type="button"
                onClick={handleLogout}
                className="text-white/40 hover:text-white transition-colors text-xs font-dm uppercase tracking-widest"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="mx-auto w-full max-w-[1800px] px-4 pb-32 pt-36 sm:px-6 sm:pt-40 xl:px-10 2xl:px-12">
        {(title || subtitle) && (
          <div className="mb-8 sm:mb-10 2xl:mb-12">
            <h1 className="text-2xl font-syne font-bold text-white sm:text-3xl">{title}</h1>
            {subtitle && <p className="text-sm text-white/40 font-dm mt-1">{subtitle}</p>}
          </div>
        )}
        {children}
      </main>

      {/* Bottom Dock */}
      {showDock && (
        <div className="fixed inset-x-0 bottom-0 z-50 h-24">
          <Dock
            items={navItems.map((item) => ({
              icon: item.icon,
              label: item.label,
              onClick: () => {
                window.location.href = item.href
              },
              className: isActive(item.href) ? "ring-1 ring-brand/50" : "",
            }))}
            panelHeight={68}
            baseItemSize={44}
            magnification={64}
            distance={200}
          />
        </div>
      )}
    </div>
  )
}
