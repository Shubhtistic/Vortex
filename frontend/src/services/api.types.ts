// ── API Response Envelope (matches backend ApiResponse.success / .error) ──
// Every endpoint — success or error — returns this shape.
// HTTPExceptions are caught by main.py and converted to ApiResponse.error()
export interface ApiResponse<T = unknown> {
  message: string
  status_code: number
  data: T | null
  meta: Record<string, unknown> | null
}

// ── Pagination Meta ──
export interface PaginationMeta {
  limit: number
  page_num: number
  total_count: number
  total_pages: number
}

// ── Auth ──
export interface LoginPayload {
  org_slug: string
  email: string
  password: string
}

// ── Organization ──
export type InviteMembershipRole = "admin" | "analyst"
export type MembershipRole = "owner" | "admin" | "analyst"

export interface SignupPayload {
  org_name: string
  slug: string
  email: string
  password: string
  first_name: string
  last_name: string
}

export interface InviteMemberPayload {
  first_name: string
  last_name: string
  password: string
  email: string
  role: InviteMembershipRole
}

export interface OrgMember {
  user_id: string
  role: MembershipRole
  email: string
  first_name: string
  last_name: string
  created_at: string
}

export interface Organization {
  id: string
  name: string
  slug: string
  is_active: boolean
  created_at: string
}

// ── User ──
export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
}

// ── Tenant ──
export type TenantStatus = "active" | "suspended" | "archived"
export type ApiKeyStatus = "active" | "grace_period" | "revoked"

export interface CreateTenantPayload {
  tenant_name: string
  slug: string
}

export interface Tenant {
  id: string
  tenant_name: string
  slug: string
  created_at: string
  status: TenantStatus
}

export interface CreateApiKeyPayload {
  api_key_slug: string
  tenant_id: string
}

export interface ApiKey {
  id: string
  api_key_slug: string
  api_key_raw_preview: string
  status: ApiKeyStatus
  raw_api_key?: string // only returned on creation
}

export interface ApiKeyRotatePayload {
  api_key_id: string
  tenant_id: string
  api_key_slug: string
}

// ── Error Response Types (all HTTPExceptions map to ApiResponse.error) ──
// These are the message strings for each known HTTPException path

// auth/dependencies.py
export type AuthErrorMessage =
  | "Invalid or expired token" // 401 — bad JWT
  | "Malformed token claims" // 401 — missing user_id/org_id
  | "Service temporarily unavailable" // 503 — DB OperationalError
  | "Not an active member of this organization" // 403 — membership not found
  | "Admin or owner role required" // 403 — insufficient role
  | "Owner role required" // 403 — owner-only endpoint
  | "Session expired, please log in again" // 401 — refresh token errors
  | "No refresh token provided" // 401 — no refresh cookie

// organizations/routers.py
export type OrgErrorMessage =
  | "Organization slug already taken / Email already taken" // 409
  | "Organization not found" // 404
  | "Email already registered or insufficient permissions" // 409
  | "This User Could not be deleted be Deleted" // 400 — owner protected

// tenants/routers.py
export type TenantErrorMessage =
  | "this slug is already taken" // 409 — duplicate tenant or api key slug
  | "This Key is already revoked or it may already be in grace period" // 409
  | "The key is already revoked or is in grace period" // 409
  | "The key slug is already taken" // 409

// Event ingestion is intentionally outside the website dashboard API client.
