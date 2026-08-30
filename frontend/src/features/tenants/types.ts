export interface TenantSettings {
  name: string
  slug: string
  plan: string
  members_count: number
  settings: Record<string, unknown>
}

export interface InviteMember {
  email: string
  role: 'admin' | 'member'
}
