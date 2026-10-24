"use client"

import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react"
import { authApi, orgApi, userApi } from "@/services/api.services"
import type { User } from "@/services/api.types"
import { setAccessToken } from "./api"
import { isValidJwtFormat, sanitizeLoginPayload, sanitizeSignupPayload } from "./validation"

interface AuthContextType {
  user: User | null
  accessToken: string | null
  login: (org_slug: string, email: string, password: string) => Promise<void>
  signup: (payload: {
    org_name: string
    slug: string
    email: string
    password: string
    first_name: string
    last_name: string
  }) => Promise<void>
  logout: () => Promise<void>
  isAuthenticated: boolean
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const initialToken =
    typeof sessionStorage !== "undefined" ? sessionStorage.getItem("access_token") : null
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessTokenState] = useState<string | null>(initialToken)
  const [loading, setLoading] = useState(true)

  const fetchUser = useCallback(async (_token: string) => {
    try {
      const res = await userApi.getMe()
      if (res?.data?.data) setUser(res.data.data)
    } catch {
      setUser(null)
    }
  }, [])

  useEffect(() => {
    if (initialToken && isValidJwtFormat(initialToken)) {
      setAccessToken(initialToken)
      setAccessTokenState(initialToken)
      fetchUser(initialToken)
    }
    setLoading(false)
  }, [initialToken, fetchUser])

  const login = useCallback(
    async (org_slug: string, email: string, password: string) => {
      const sanitized = sanitizeLoginPayload({ org_slug, email, password })
      const res = await authApi.login(sanitized.org_slug, sanitized.email, sanitized.password)
      const token = res.data?.data?.access_token
      if (token && isValidJwtFormat(token)) {
        setAccessToken(token)
        setAccessTokenState(token)
        sessionStorage.setItem("access_token", token)
        await fetchUser(token)
      } else {
        throw new Error("Invalid token received from server")
      }
    },
    [fetchUser]
  )

  const signup = useCallback(
    async (payload: {
      org_name: string
      slug: string
      email: string
      password: string
      first_name: string
      last_name: string
    }) => {
      const sanitized = sanitizeSignupPayload(payload)
      await orgApi.signup(sanitized)
    },
    []
  )

  const logout = useCallback(async () => {
    await authApi.logout()
    setAccessToken(null)
    setAccessTokenState(null)
    setUser(null)
    sessionStorage.removeItem("access_token")
  }, [])

  const isAuthenticated = !!accessToken

  return (
    <AuthContext.Provider
      value={{ user, accessToken, login, signup, logout, isAuthenticated, loading }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
