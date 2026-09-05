"use client"

import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react"
import api, { setAccessToken } from "./api"

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
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessTokenState] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = sessionStorage.getItem("access_token")
    if (token) {
      setAccessToken(token)
      setAccessTokenState(token)
    }
    setLoading(false)
  }, [])

  const login = useCallback(async (org_slug: string, email: string, password: string) => {
    const res = await api.post("/auth/login", { org_slug, email, password })
    const token = res.data?.data?.access_token
    if (token) {
      setAccessToken(token)
      setAccessTokenState(token)
      sessionStorage.setItem("access_token", token)
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
      await api.post("/organizations/signup", payload)
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

  return (
    <AuthContext.Provider
      value={{ user, accessToken, login, signup, logout, isAuthenticated: !!accessToken, loading }}
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
