import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTenantSettings, updateTenantSettings, inviteMember } from './api'

export function useTenantSettings() {
  return useQuery({
    queryKey: ['tenant', 'settings'],
    queryFn: getTenantSettings,
  })
}

export function useUpdateTenantSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (settings: Record<string, unknown>) => updateTenantSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenant', 'settings'] })
    },
  })
}

export function useInviteMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ email, role }: { email: string; role: 'admin' | 'member' }) =>
      inviteMember(email, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenant', 'settings'] })
    },
  })
}
