export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'member'
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface TeamMember extends User {
  last_login_at?: string
}
