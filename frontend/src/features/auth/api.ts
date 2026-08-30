import type { AxiosResponse } from 'axios'
import { api } from '@lib/apiClient'
import type { AuthUser, BootstrapData } from './types'

export async function login(credentials: {
  email: string
  password: string
}): Promise<{ access_token: string; user: AuthUser }> {
  const response: AxiosResponse<{ access_token: string; user: AuthUser }> = await api.post('/api/auth/login', credentials)
  return response.data
}

export async function bootstrap(data: BootstrapData): Promise<{
  access_token: string
  user: AuthUser
}> {
  const response: AxiosResponse<{ access_token: string; user: AuthUser }> = await api.post('/api/auth/bootstrap', data)
  return response.data
}

export async function checkAuth(): Promise<AuthUser | null> {
  try {
    const response: AxiosResponse<AuthUser> = await api.get('/api/auth/me')
    return response.data
  } catch {
    return null
  }
}
