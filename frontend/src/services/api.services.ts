import api from "@/lib/api"
import type {
  ApiKey,
  ApiKeyRotatePayload,
  CreateApiKeyPayload,
  CreateTenantPayload,
  InviteMemberPayload,
  Organization,
  OrgMember,
  PaginationMeta,
  SignupPayload,
  Tenant,
  User,
} from "./api.types"

// ── Auth ──
export const authApi = {
  login: (org_slug: string, email: string, password: string) =>
    api.post<{ data: { access_token: string } }>("/auth/login", {
      org_slug,
      email,
      password,
    }),

  logout: () => api.post("/auth/logout"),
}

// ── User / Me ──
export const userApi = {
  getMe: () => api.get<{ data: User }>("/users/me").catch(() => null),
}

// ── Organization ──
export const orgApi = {
  signup: (payload: SignupPayload) => api.post("/organizations/signup", payload),

  getMe: () => api.get<{ data: Organization }>("/organizations/me").catch(() => null),

  getMembers: (params?: { limit?: number; page_num?: number }) =>
    api.get<{
      data: OrgMember[]
      meta: PaginationMeta
    }>("/organizations/members", { params }),

  inviteMember: (payload: InviteMemberPayload) => api.post("/organizations/invite", payload),

  deactivateMember: (userId: string) => api.delete(`/organizations/members/${userId}`),
}

// ── Tenant ──
export const tenantApi = {
  list: (params?: { limit?: number; page_num?: number }) =>
    api.get<{
      data: Tenant[]
      meta: PaginationMeta
    }>("/tenants", { params }),

  create: (payload: CreateTenantPayload) => api.post<{ data: Tenant }>("/tenants", payload),

  findById: async (tenantId: string): Promise<Tenant | null> => {
    const firstPage = await tenantApi.list({ limit: 50, page_num: 1 })
    const firstPageTenant = firstPage.data.data?.find((tenant) => tenant.id === tenantId)
    if (firstPageTenant) return firstPageTenant

    const totalPages = firstPage.data.meta?.total_pages ?? 1
    for (let pageNum = 2; pageNum <= totalPages; pageNum += 1) {
      const page = await tenantApi.list({ limit: 50, page_num: pageNum })
      const tenant = page.data.data?.find((item) => item.id === tenantId)
      if (tenant) return tenant
    }

    return null
  },
}

// ── ApiKey ──
export const apiKeyApi = {
  list: (tenantId: string, params?: { limit?: number; page_num?: number }) =>
    api.get<{
      data: ApiKey[]
      meta: PaginationMeta
    }>("/tenants/api-keys", { params: { tenant_id: tenantId, ...params } }),

  create: (payload: CreateApiKeyPayload) => api.post<{ data: ApiKey }>("/tenants/api-key", payload),

  revoke: (tenantId: string, apiKeyId: string) =>
    api.delete(`/tenants/${tenantId}/api-keys/${apiKeyId}`),

  rotate: (payload: ApiKeyRotatePayload) =>
    api.post<{ data: ApiKey }>("/tenants/api-keys/rotate", payload),
}
