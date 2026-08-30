import { useQuery, useMutation } from '@tanstack/react-query'
import { login, bootstrap, checkAuth } from './api'

export function useAuth() {
  return useQuery({
    queryKey: ['auth'],
    queryFn: checkAuth,
    retry: false,
  })
}

export function useLogin() {
  return useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      login(credentials),
  })
}

export function useBootstrap() {
  return useMutation({
    mutationFn: (data: {
      email: string
      password: string
      tenant_name: string
    }) => bootstrap(data),
  })
}
