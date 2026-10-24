"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { useEffect, useState } from "react"
import DashboardShell from "@/components/dashboard/DashboardShell"
import Badge from "@/components/ui/Badge"
import Button from "@/components/ui/Button"
import Card from "@/components/ui/Card"
import Input from "@/components/ui/Input"
import Modal from "@/components/ui/Modal"
import { apiKeyApi, tenantApi } from "@/services/api.services"
import type { ApiKey, ApiKeyRotatePayload, CreateApiKeyPayload, Tenant } from "@/services/api.types"

export default function TenantDetailPage() {
  const params = useParams<{ id: string }>()
  const tenantId = params.id

  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [rotating, setRotating] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [rotateOpen, setRotateOpen] = useState(false)
  const [selectedKey, setSelectedKey] = useState<ApiKey | null>(null)
  const [newSlug, setNewSlug] = useState("")
  const [createError, setCreateError] = useState("")
  const [rotateError, setRotateError] = useState("")
  const [showRawKey, setShowRawKey] = useState(false)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [tenantData, keysRes] = await Promise.all([
          tenantApi.findById(tenantId),
          apiKeyApi.list(tenantId, { limit: 50 }),
        ])
        setTenant(tenantData)
        if (keysRes?.data?.data) setKeys(keysRes.data.data)
      } catch (err) {
        const msg =
          err instanceof Error && "frontendMessage" in err
            ? (err as { frontendMessage: string }).frontendMessage
            : String(err)
        console.error("[tenant detail] loadData failed:", msg)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [tenantId])

  const handleCreateKey = async () => {
    setCreateError("")
    if (!newSlug) {
      setCreateError("Slug is required")
      return
    }
    setCreating(true)
    try {
      const payload: CreateApiKeyPayload = { api_key_slug: newSlug, tenant_id: tenantId }
      const res = await apiKeyApi.create(payload)
      if (res?.data?.data) {
        setKeys((prev) => [...prev, res.data.data])
        setCreateOpen(false)
        setNewSlug("")
        setShowRawKey(true)
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error && "response" in err
          ? ((err as { response?: { data?: { message?: string } } }).response?.data?.message ??
            "Failed to create key")
          : "Failed to create key"
      setCreateError(message)
    } finally {
      setCreating(false)
    }
  }

  const handleRotate = async (key: ApiKey) => {
    setRotateError("")
    setSelectedKey(key)
    setRotateOpen(true)
  }

  const confirmRotate = async () => {
    if (!selectedKey) return
    setRotateError("")
    setRotating(selectedKey.id)
    try {
      const payload: ApiKeyRotatePayload = {
        api_key_id: selectedKey.id,
        tenant_id: tenantId,
        api_key_slug: newSlug || selectedKey.api_key_slug,
      }
      const res = await apiKeyApi.rotate(payload)
      if (res?.data?.data) {
        setKeys((prev) =>
          prev.map((k) => (k.id === selectedKey.id ? (res.data.data as ApiKey) : k))
        )
        setRotateOpen(false)
        setNewSlug("")
        setShowRawKey(true)
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error && "response" in err
          ? ((err as { response?: { data?: { message?: string } } }).response?.data?.message ??
            "Failed to rotate key")
          : "Failed to rotate key"
      setRotateError(message)
    } finally {
      setRotating(null)
    }
  }

  const handleRevoke = async (key: ApiKey) => {
    if (!window.confirm(`Revoke API key "${key.api_key_slug}"? It will enter a grace period.`))
      return
    try {
      await apiKeyApi.revoke(tenantId, key.id)
      setKeys((prev) =>
        prev.map((k) => (k.id === key.id ? { ...k, status: "revoked" as const } : k))
      )
    } catch {
      // silent fail
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <span className="font-dm text-white/60 text-sm tracking-widest uppercase">Loading...</span>
      </div>
    )
  }

  if (!tenant) {
    return (
      <DashboardShell title="Tenant not found" showDock={false}>
        <div className="text-center py-16">
          <p className="text-white/40 font-dm">Tenant could not be loaded.</p>
          <Link
            href="/dashboard/tenants"
            className="text-brand hover:text-brand-dark mt-4 inline-block text-sm font-dm"
          >
            ← Back to Tenants
          </Link>
        </div>
      </DashboardShell>
    )
  }

  return (
    <DashboardShell title={tenant.tenant_name} subtitle={`@${tenant.slug}`} showDock={false}>
      {/* Tenant Info */}
      <Card className="mb-8" title="Tenant Info" subtitle={`ID: ${tenant.id}`}>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-white/40 font-dm text-xs uppercase tracking-widest mb-1">Slug</p>
            <p className="font-dm text-white/70">{tenant.slug}</p>
          </div>
          <div>
            <p className="text-white/40 font-dm text-xs uppercase tracking-widest mb-1">Created</p>
            <p className="font-dm text-white/70">
              {new Date(tenant.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </Card>

      {/* API Keys */}
      <Card
        title="API Keys"
        subtitle={`${keys.length} keys`}
        action={
          <Button onClick={() => setCreateOpen(true)} size="sm">
            Create Key
          </Button>
        }
        className="mb-8"
      >
        {keys.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-white/30 font-dm text-sm">No API keys yet</p>
            <Button
              variant="secondary"
              size="sm"
              className="mt-4"
              onClick={() => setCreateOpen(true)}
            >
              Create API Key
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {keys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between py-3 border-b border-[var(--color-border)] last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-brand/10 border border-brand/20 flex items-center justify-center">
                    <svg
                      className="w-4 h-4 text-brand"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-white font-dm">{key.api_key_slug}</p>
                    <p className="text-xs text-white/40 font-dm">···{key.api_key_raw_preview}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      key.status === "active"
                        ? "success"
                        : key.status === "grace_period"
                          ? "warning"
                          : "danger"
                    }
                  >
                    {key.status}
                  </Badge>
                  {key.status === "active" && (
                    <>
                      <Button variant="ghost" size="sm" onClick={() => handleRotate(key)}>
                        Rotate
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleRevoke(key)}>
                        Revoke
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Create Key Modal */}
      <Modal
        isOpen={createOpen}
        onClose={() => {
          setCreateOpen(false)
          setCreateError("")
          setShowRawKey(false)
        }}
        title="Create API Key"
        subtitle="Generate a new API key for this tenant"
        footer={
          <>
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateKey} disabled={creating}>
              {creating ? "Creating..." : "Create Key"}
            </Button>
          </>
        }
      >
        {showRawKey ? (
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-[var(--color-accent2)]/10 border border-[var(--color-accent2)]/20">
              <p className="text-xs text-[var(--color-accent2)] font-dm mb-1">
                Save this key — it won&apos;t be shown again
              </p>
              <p className="text-sm text-white font-dm break-all">
                {keys[keys.length - 1]?.raw_api_key ?? "—"}
              </p>
            </div>
          </div>
        ) : (
          <>
            {createError && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-dm">
                {createError}
              </div>
            )}
            <Input
              label="Key slug"
              value={newSlug}
              onChange={setNewSlug}
              placeholder="my-service-key"
              maxLength={20}
            />
          </>
        )}
      </Modal>

      {/* Rotate Key Modal */}
      <Modal
        isOpen={rotateOpen}
        onClose={() => {
          setRotateOpen(false)
          setRotateError("")
          setShowRawKey(false)
          setNewSlug("")
        }}
        title="Rotate API Key"
        subtitle={`Rotating "${selectedKey?.api_key_slug}"`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setRotateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={confirmRotate} disabled={rotating !== null}>
              {rotating === selectedKey?.id ? "Rotating..." : "Rotate Key"}
            </Button>
          </>
        }
      >
        {showRawKey ? (
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-[var(--color-accent2)]/10 border border-[var(--color-accent2)]/20">
              <p className="text-xs text-[var(--color-accent2)] font-dm mb-1">
                New key generated — save it now
              </p>
              <p className="text-sm text-white font-dm break-all">
                {keys.find((k) => k.id === selectedKey?.id)?.raw_api_key ?? "—"}
              </p>
            </div>
          </div>
        ) : (
          <>
            {rotateError && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-dm">
                {rotateError}
              </div>
            )}
            <p className="text-sm text-white/60 font-dm mb-4">
              Enter a new slug for the rotated key. The old key will enter a grace period.
            </p>
            <Input
              label="New key slug"
              value={newSlug}
              onChange={setNewSlug}
              placeholder="my-service-key-v2"
              maxLength={20}
            />
          </>
        )}
      </Modal>
    </DashboardShell>
  )
}
