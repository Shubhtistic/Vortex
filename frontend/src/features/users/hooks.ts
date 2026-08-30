import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTeamMembers, inviteMember, removeMember } from './api'

export function useTeamMembers() {
  return useQuery({
    queryKey: ['team-members'],
    queryFn: getTeamMembers,
  })
}

export function useInviteMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { email: string; role: 'admin' | 'member' }) =>
      inviteMember(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team-members'] })
    },
  })
}

export function useRemoveMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userId: string) => removeMember(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team-members'] })
    },
  })
}
