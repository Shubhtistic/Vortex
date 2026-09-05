// ── Input sanitization & validation utilities ──────────────────────────────
// All functions are pure. No SSR/CSR assumptions. No backend calls.

// Trim leading/trailing whitespace (handles NBSP, tabs, newlines)
export function trim(value: string): string {
  return value.replace(/^[\s\u00A0]+/, "").replace(/[\s\u00A0]+$/, "")
}

// Strip multiple internal spaces, collapse to single, trim edges
export function normalizeSpaces(value: string): string {
  return value.replace(/[\s\u00A0]+/g, " ").trim()
}

// Allow only alphanumeric, hyphens, underscores, dots (safe slug charset)
export function normalizeSlug(value: string): string {
  return trim(value)
    .toLowerCase()
    .replace(/[^a-z0-9._-]/g, "")
    .replace(/_/, "-")
    .replace(/-+/g, "-")
}

// Validate email (basic RFC 5322 pattern; backend validates fully)
export function isValidEmail(email: string): boolean {
  const cleaned = trim(email)
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleaned)
}

// Validate org slug (lowercase alphanum, hyphens, max 50 chars)
export function isValidSlug(slug: string): boolean {
  const cleaned = trim(slug)
  return /^[a-z0-9][a-z0-9-]{0,49}$/.test(cleaned)
}

// HTML-escape to prevent XSS when rendering user-provided strings in JSX
export function escapeHtml(value: string): string {
  const map: Record<string, string> = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
    "/": "&#x2F;",
  }
  return value.replace(/[&<>"'/]/g, (char) => map[char])
}

// Validate password (min 8, max 256, no control characters)
export function isValidPassword(password: string): boolean {
  const cleaned = trim(password)
  return (
    cleaned.length >= 8 && cleaned.length <= 256 && !/[^\u0020-\u007E]/.test(cleaned) // allow only printable ASCII
  )
}

// Validate a display name (letters, numbers, spaces, hyphens; max 100 chars)
export function isValidName(name: string): boolean {
  const normalized = normalizeSpaces(name)
  return (
    normalized.length > 0 && normalized.length <= 100 && /^[a-zA-Z0-9\s\-'.]+$/.test(normalized)
  )
}

// Sanitize all text fields for a signup payload
export function sanitizeSignupPayload(payload: {
  org_name: string
  slug: string
  email: string
  password: string
  first_name: string
  last_name: string
}): {
  org_name: string
  slug: string
  email: string
  password: string
  first_name: string
  last_name: string
} {
  return {
    org_name: escapeHtml(normalizeSpaces(trim(payload.org_name))),
    slug: normalizeSlug(payload.slug),
    email: trim(payload.email).toLowerCase(),
    password: trim(payload.password),
    first_name: escapeHtml(normalizeSpaces(trim(payload.first_name))),
    last_name: escapeHtml(normalizeSpaces(trim(payload.last_name))),
  }
}

// Sanitize login credentials
export function sanitizeLoginPayload(payload: {
  org_slug: string
  email: string
  password: string
}): { org_slug: string; email: string; password: string } {
  return {
    org_slug: normalizeSlug(payload.org_slug),
    email: trim(payload.email).toLowerCase(),
    password: trim(payload.password),
  }
}

// Validate a JWT token format (header.payload.signature, each base64url)
export function isValidJwtFormat(token: string): boolean {
  return (
    typeof token === "string" &&
    token.split(".").length === 3 &&
    token.split(".").every((part) => /^[A-Za-z0-9_-]+$/.test(part) && part.length > 0)
  )
}
