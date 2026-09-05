"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { useAuth } from "@/lib/auth-context"
import {
  isValidEmail,
  isValidName,
  isValidSlug,
  sanitizeSignupPayload,
  trim,
} from "@/lib/validation"

export default function SignupPage() {
  const router = useRouter()
  const { signup, isAuthenticated } = useAuth()
  const [orgName, setOrgName] = useState("")
  const [slug, setSlug] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/")
    }
  }, [isAuthenticated, router])

  const handleSlugChange = (raw: string) => {
    setSlug(
      trim(raw)
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, "")
        .replace(/-+/g, "-")
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    const trimmedOrgName = trim(orgName)
    const trimmedSlug = trim(slug)
    const trimmedEmail = trim(email)
    const trimmedPassword = trim(password)
    const trimmedFirstName = trim(firstName)
    const trimmedLastName = trim(lastName)

    if (!trimmedOrgName || trimmedOrgName.length < 2) {
      setError("Organization name must be at least 2 characters")
      return
    }
    if (!trimmedSlug || !isValidSlug(trimmedSlug)) {
      setError("Slug must be lowercase letters, numbers, and hyphens (e.g. acme-corp)")
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
    if (!trimmedFirstName || !isValidName(trimmedFirstName)) {
      setError("Invalid first name")
      return
    }
    if (!trimmedLastName || !isValidName(trimmedLastName)) {
      setError("Invalid last name")
      return
    }

    setLoading(true)
    try {
      const sanitized = sanitizeSignupPayload({
        org_name: trimmedOrgName,
        slug: trimmedSlug,
        email: trimmedEmail,
        password: trimmedPassword,
        first_name: trimmedFirstName,
        last_name: trimmedLastName,
      })
      await signup(sanitized)
      router.replace("/login")
    } catch (err: unknown) {
      const message =
        err instanceof Error && "response" in err
          ? ((err as { response?: { data?: { message?: string } } }).response?.data?.message ??
            "Signup failed")
          : "Signup failed"
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="font-syne text-2xl font-bold text-white tracking-tight">
            Vortex
          </Link>
          <p className="mt-2 text-sm text-white/50 font-dm">Create your organization</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-dm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="firstName"
                className="block text-xs uppercase tracking-widest text-white/50 font-dm mb-2"
              >
                First name
              </label>
              <input
                id="firstName"
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
                maxLength={100}
                autoComplete="given-name"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white font-dm text-sm placeholder-white/20 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/50 transition-colors"
                placeholder="Jane"
              />
            </div>
            <div>
              <label
                htmlFor="lastName"
                className="block text-xs uppercase tracking-widest text-white/50 font-dm mb-2"
              >
                Last name
              </label>
              <input
                id="lastName"
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
                maxLength={100}
                autoComplete="family-name"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white font-dm text-sm placeholder-white/20 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/50 transition-colors"
                placeholder="Doe"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="orgName"
              className="block text-xs uppercase tracking-widest text-white/50 font-dm mb-2"
            >
              Organization name
            </label>
            <input
              id="orgName"
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              required
              maxLength={100}
              autoComplete="organization"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white font-dm text-sm placeholder-white/20 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/50 transition-colors"
              placeholder="Acme Corp"
            />
          </div>

          <div>
            <label
              htmlFor="slug"
              className="block text-xs uppercase tracking-widest text-white/50 font-dm mb-2"
            >
              Organization slug
            </label>
            <input
              id="slug"
              type="text"
              value={slug}
              onChange={(e) => handleSlugChange(e.target.value)}
              required
              maxLength={50}
              autoComplete="organization"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white font-dm text-sm placeholder-white/20 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/50 transition-colors"
              placeholder="acme-corp"
            />
            <p className="mt-1 text-xs text-white/30 font-dm">
              Used as your org identifier (e.g. acme-corp.vortex.app)
            </p>
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
              minLength={8}
              autoComplete="new-password"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white font-dm text-sm placeholder-white/20 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/50 transition-colors"
              placeholder="Minimum 8 characters"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand hover:bg-brand-dark text-white font-syne font-semibold py-3 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-white/40 font-dm">
          Already have an account?{" "}
          <Link href="/login" className="text-brand hover:text-brand-dark transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
