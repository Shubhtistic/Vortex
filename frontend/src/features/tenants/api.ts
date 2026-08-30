import type { AxiosResponse } from 'axios'
import { api } from '@lib/apiClient'
import type { TenantSettings } from './types'

export async function getTenantSettings(): Promise<TenantSettings> {
  const response: AxiosResponse<TenantSettings> = await api.get('/api/tenants/settings')
  return response.data
}

export async function updateTenantSettings(settings: Record<string, unknown>): Promise<TenantSettings> {
  const response: AxiosResponse<TenantSettings> = await api.patch('/api/tenants/settings', settings)
  return response.data
}

export async function inviteMember(email: string, role: 'admin' | 'member'): Promise<{ message: string }> {
  const response: AxiosResponse<{ message: string }> = await api.post('/api/tenants/members/invite', { email, role })
  return response.data
}
