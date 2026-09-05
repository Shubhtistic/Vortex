"use client"

import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react"
import api, { setAccessToken } from "./api"
import { isValidJwtFormat, sanitizeLoginPayload, sanitizeSignupPayload } from "./validation"

interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  is_email_verified: boolean
}

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

  useEffect(() => {
    if (initialToken && isValidJwtFormat(initialToken)) {
      setAccessToken(initialToken)
    }
  }, [initialToken])

  const login = useCallback(async (org_slug: string, email: string, password: string) => {
    const sanitized = sanitizeLoginPayload({ org_slug, email, password })
    const res = await api.post("/auth/login", sanitized)
    const token = res.data?.data?.access_token
    if (token && isValidJwtFormat(token)) {
      setAccessToken(token)
      setAccessTokenState(token)
      sessionStorage.setItem("access_token", token)
    } else {
      throw new Error("Invalid token received from server")
    }
  }, [])

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
      await api.post("/organizations/signup", sanitized)
    },
    []
  )

  const logout = useCallback(async () => {
    await api.post("/auth/logout")
    setAccessToken(null)
    setAccessTokenState(null)
    setUser(null)
    sessionStorage.removeItem("access_token")
  }, [])

  const isAuthenticated = !!accessToken

  return (
    <AuthContext.Provider
      value={{ user, accessToken, login, signup, logout, isAuthenticated, loading: false }}
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
