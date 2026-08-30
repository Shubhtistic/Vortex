import type { AxiosResponse } from 'axios'
import { api } from '@lib/apiClient'
import type { TeamMember } from './types'

export async function getTeamMembers(): Promise<TeamMember[]> {
  const response: AxiosResponse<TeamMember[]> = await api.get('/api/tenants/members')
  return response.data
}

export async function inviteMember(data: {
  email: string
  role: 'admin' | 'member'
}): Promise<{ message: string }> {
  const response: AxiosResponse<{ message: string }> = await api.post('/api/tenants/members/invite', data)
  return response.data
}

export async function removeMember(userId: string): Promise<void> {
  await api.delete(`/api/tenants/members/${userId}`)
}
