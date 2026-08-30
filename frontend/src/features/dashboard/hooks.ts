import { useQuery } from '@tanstack/react-query'
import { getDashboardData, getEventsPerDay, getTopUrls } from './api'
import type { DashboardStats, EventDay, TopUrl } from './types'

export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ['dashboard', 'stats'],
    queryFn: getDashboardData,
  })
}

export function useEventsPerDay(days = 7) {
  return useQuery<EventDay[]>({
    queryKey: ['dashboard', 'events', days],
    queryFn: () => getEventsPerDay(days),
  })
}

export function useTopUrls(limit = 10) {
  return useQuery<TopUrl[]>({
    queryKey: ['dashboard', 'top-urls', limit],
    queryFn: () => getTopUrls(limit),
  })
}
