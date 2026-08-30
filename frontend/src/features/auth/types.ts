export interface AuthUser {
  id: string
  email: string
  name: string
  tenant_id: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface BootstrapData {
  email: string
  password: string
  tenant_name: string
}
