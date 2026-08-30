import type { AxiosResponse } from 'axios'
import { api } from '@lib/apiClient'
import type { DashboardStats, EventDay, TopUrl } from './types'

export async function getDashboardData(): Promise<DashboardStats> {
  const response: AxiosResponse<DashboardStats> = await api.get('/api/dashboard')
  return response.data
}

export async function getEventsPerDay(days: number): Promise<EventDay[]> {
  const response: AxiosResponse<EventDay[]> = await api.get(`/api/dashboard/events?days=${days}`)
  return response.data
}

export async function getTopUrls(limit: number = 10): Promise<TopUrl[]> {
  const response: AxiosResponse<TopUrl[]> = await api.get(`/api/dashboard/top-urls?limit=${limit}`)
  return response.data
}
