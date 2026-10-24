import api from "@/lib/api"
import type {
  AnalyticsActiveUsersPoint,
  AnalyticsBreakdownValue,
  AnalyticsFilters,
  AnalyticsOverview,
  AnalyticsRecentEvent,
  AnalyticsTimePoint,
  AnalyticsTopEvent,
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

  listAll: async (): Promise<Tenant[]> => {
    const firstPage = await tenantApi.list({ limit: 50, page_num: 1 })
    const tenants = firstPage.data.data ?? []
    const totalPages = firstPage.data.meta?.total_pages ?? 1
    if (totalPages <= 1) return tenants

    const remainingPages = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, index) =>
        tenantApi.list({ limit: 50, page_num: index + 2 })
      )
    )
    return tenants.concat(...remainingPages.map((page) => page.data.data ?? []))
  },

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

// ── Analytics ──
export const analyticsApi = {
  overview: (params: AnalyticsFilters) =>
    api.get<{ data: AnalyticsOverview }>("/analytics/overview", { params }),

  timeseries: (params: AnalyticsFilters, interval: "hour" | "day") =>
    api.get<{ data: AnalyticsTimePoint[] }>("/analytics/timeseries", {
      params: { ...params, interval },
    }),

  topEvents: (params: AnalyticsFilters, limit = 10) =>
    api.get<{ data: AnalyticsTopEvent[] }>("/analytics/top-events", {
      params: { ...params, limit },
    }),

  breakdown: (params: AnalyticsFilters, property: string, limit = 8) =>
    api.get<{ data: AnalyticsBreakdownValue[] }>("/analytics/breakdown", {
      params: { ...params, property, limit },
    }),

  activeUsers: (params: AnalyticsFilters, interval: "day" | "week" | "month") =>
    api.get<{ data: AnalyticsActiveUsersPoint[] }>("/analytics/active-users", {
      params: { ...params, interval },
    }),

  recentEvents: (params: AnalyticsFilters, limit = 30) =>
    api.get<{ data: AnalyticsRecentEvent[] }>("/analytics/events/recent", {
      params: { ...params, limit },
    }),
}
