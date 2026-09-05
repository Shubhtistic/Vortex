"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { useAuth } from "@/lib/auth-context"
import { isValidEmail, isValidSlug, sanitizeLoginPayload, trim } from "@/lib/validation"

export default function LoginPage() {
  const router = useRouter()
  const { login, isAuthenticated } = useAuth()
  const [orgSlug, setOrgSlug] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/")
    }
  }, [isAuthenticated, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    const trimmedSlug = trim(orgSlug)
    const trimmedEmail = trim(email)
    const trimmedPassword = trim(password)

    if (!trimmedSlug || !isValidSlug(trimmedSlug)) {
      setError("Invalid organization slug")
      return
    }
    if (!trimmedEmail || !isValidEmail(trimmedEmail)) {
      setError("Invalid email address")
      return
    }
    if (!trimmedPassword || trimmedPassword.length < 8) {
      setError("Password must be at least 8 characters")
      return
    }

    setLoading(true)
    try {
      const sanitized = sanitizeLoginPayload({
        org_slug: trimmedSlug,
        email: trimmedEmail,
        password: trimmedPassword,
      })
      await login(sanitized.org_slug, sanitized.email, sanitized.password)
      router.replace("/")
    } catch (err: unknown) {
      const message =
        err instanceof Error && "response" in err
          ? ((err as { response?: { data?: { message?: string } } }).response?.data?.message ??
            "Login failed")
          : "Login failed"
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="font-syne text-2xl font-bold text-white tracking-tight">
            Vortex
          </Link>
          <p className="mt-2 text-sm text-white/50 font-dm">Sign in to your organization</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-dm">
              {error}
            </div>
          )}

          <div>
            <label
              htmlFor="orgSlug"
              className="block text-xs uppercase tracking-widest text-white/50 font-dm mb-2"
            >
              Organization slug
            </label>
            <input
              id="orgSlug"
              type="text"
              value={orgSlug}
              onChange={(e) => setOrgSlug(e.target.value)}
              required
              autoComplete="organization"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white font-dm text-sm placeholder-white/20 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/50 transition-colors"
              placeholder="my-org"
            />
          </div>

          <div>
            <label
              htmlFor="email"
              className="block text-xs uppercase tracking-widest text-white/50 font-dm mb-2"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white font-dm text-sm placeholder-white/20 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/50 transition-colors"
              placeholder="you@company.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-xs uppercase tracking-widest text-white/50 font-dm mb-2"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              minLength={8}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white font-dm text-sm placeholder-white/20 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/50 transition-colors"
              placeholder="Minimum 8 characters"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand hover:bg-brand-dark text-white font-syne font-semibold py-3 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-white/40 font-dm">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="text-brand hover:text-brand-dark transition-colors">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}
