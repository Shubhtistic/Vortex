"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import DashboardShell from "@/components/dashboard/DashboardShell"
import Badge from "@/components/ui/Badge"
import Button from "@/components/ui/Button"
import Card from "@/components/ui/Card"
import EmptyState from "@/components/ui/EmptyState"
import Input from "@/components/ui/Input"
import Modal from "@/components/ui/Modal"
import { tenantApi } from "@/services/api.services"
import type { CreateTenantPayload, Tenant } from "@/services/api.types"

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState("")
  const [tenantName, setTenantName] = useState("")
  const [slug, setSlug] = useState("")

  useEffect(() => {
    tenantApi
      .list({ limit: 50 })
      .then((res) => {
        if (res?.data?.data) setTenants(res.data.data)
      })
      .catch((err: unknown) => {
        const msg =
          err instanceof Error && "frontendMessage" in err
            ? (err as { frontendMessage: string }).frontendMessage
            : "Failed to load tenants"
        setError(msg)
      })
      .finally(() => setLoading(false))
  }, [])

  const handleCreate = async () => {
    setError("")
    if (!tenantName || !slug) {
      setError("Both fields are required")
      return
    }
    setCreating(true)
    try {
      const payload: CreateTenantPayload = { tenant_name: tenantName, slug }
      await tenantApi.create(payload)
      setCreateOpen(false)
      setTenantName("")
      setSlug("")
      const res = await tenantApi.list({ limit: 50 })
      if (res?.data?.data) setTenants(res.data.data)
    } catch (err: unknown) {
      const message =
        err instanceof Error && "response" in err
          ? ((err as { response?: { data?: { message?: string } } }).response?.data?.message ??
            "Failed to create tenant")
          : "Failed to create tenant"
      setError(message)
    } finally {
      setCreating(false)
    }
  }

  const handleSlugChange = (raw: string) => {
    setSlug(
      raw
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, "")
        .replace(/-+/g, "-")
    )
  }

  if (loading) {
    return (
      <DashboardShell title="Tenants" subtitle="Loading tenants">
        <div className="flex min-h-40 items-center justify-center">
          <span className="font-dm text-sm uppercase tracking-widest text-white/60">
            Loading...
          </span>
        </div>
      </DashboardShell>
    )
  }

  return (
    <DashboardShell title="Tenants" subtitle={`${tenants.length} tenants`}>
      <div className="mb-8">
        <Button onClick={() => setCreateOpen(true)} size="sm">
          Create Tenant
        </Button>
      </div>

      <Card>
        {tenants.length === 0 ? (
          <EmptyState
            title="No tenants yet"
            description="Create your first tenant to start managing API keys and services."
            action={
              <Button onClick={() => setCreateOpen(true)} size="sm">
                Create Tenant
              </Button>
            }
          />
        ) : (
          <div className="space-y-3">
            {tenants.map((tenant) => (
              <Link
                key={tenant.id}
                href={`/dashboard/tenants/${tenant.id}`}
                className="flex items-center justify-between py-3 border-b border-[var(--color-border)] last:border-0 hover:bg-white/5 rounded-lg px-3 -mx-3 transition-colors"
              >
                <div>
                  <p className="text-sm text-white font-dm">{tenant.tenant_name}</p>
                  <p className="text-xs text-white/40 font-dm">{tenant.slug}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge
                    variant={
                      tenant.status === "active"
                        ? "success"
                        : tenant.status === "suspended"
                          ? "warning"
                          : "default"
                    }
                  >
                    {tenant.status}
                  </Badge>
                  <svg
                    className="w-4 h-4 text-white/30"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>

      <Modal
        isOpen={createOpen}
        onClose={() => {
          setCreateOpen(false)
          setError("")
        }}
        title="Create Tenant"
        subtitle="Add a new tenant to your organization"
        footer={
          <>
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={creating}>
              {creating ? "Creating..." : "Create Tenant"}
            </Button>
          </>
        }
      >
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-dm">
            {error}
          </div>
        )}
        <div className="space-y-4">
          <Input
            label="Tenant name"
            value={tenantName}
            onChange={setTenantName}
            placeholder="Acme Production"
            maxLength={50}
          />
          <Input
            label="Slug"
            value={slug}
            onChange={handleSlugChange}
            placeholder="acme-prod"
            maxLength={20}
          />
          <p className="text-xs text-white/30 font-dm">
            Used as identifier for API keys and tenant-specific operations.
          </p>
        </div>
      </Modal>
    </DashboardShell>
  )
}
