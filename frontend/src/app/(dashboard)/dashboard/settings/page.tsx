"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import DashboardShell from "@/components/dashboard/DashboardShell"
import Card from "@/components/ui/Card"
import { orgApi, userApi } from "@/services/api.services"
import type { Organization, User } from "@/services/api.types"

export default function SettingsPage() {
  const [org, setOrg] = useState<Organization | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")

  useEffect(() => {
    const loadData = async () => {
      try {
        const [orgRes, userRes] = await Promise.all([orgApi.getMe(), userApi.getMe()])
        const organization = orgRes?.data?.data ?? null
        const account = userRes?.data?.data ?? null

        setOrg(organization)
        setUser(account)
        if (!organization || !account) {
          setLoadError("Some account details could not be loaded. Try refreshing the page.")
        }
      } catch {
        setLoadError("Account details could not be loaded. Try refreshing the page.")
      } finally {
        setLoading(false)
      }
    }

    void loadData()
  }, [])

  if (loading) {
    return (
      <DashboardShell title="Settings" subtitle="Your account and organization details">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
          <p className="font-dm text-sm text-white/50">Loading account details...</p>
        </div>
      </DashboardShell>
    )
  }

  const initials = `${user?.first_name?.[0] ?? ""}${user?.last_name?.[0] ?? ""}` || "V"

  return (
    <DashboardShell title="Settings" subtitle="Your account and organization details">
      <div className="max-w-5xl space-y-6">
        {loadError && (
          <div
            role="status"
            className="rounded-lg border border-[var(--color-accent3)]/25 bg-[var(--color-accent3)]/10 px-4 py-3 font-dm text-sm text-[var(--color-accent3)]"
          >
            {loadError}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Card title="Personal account" subtitle="Your signed-in user profile">
            <div className="flex items-center gap-4 border-b border-[var(--color-border)] pb-5">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-brand/30 bg-brand/10 font-syne text-sm font-bold text-brand">
                {initials}
              </div>
              <div className="min-w-0">
                <p className="truncate font-syne text-base font-semibold text-white">
                  {user ? `${user.first_name} ${user.last_name}` : "Account unavailable"}
                </p>
                <p className="truncate font-dm text-sm text-white/45">{user?.email ?? "—"}</p>
              </div>
            </div>

            <dl className="mt-5 grid gap-5 sm:grid-cols-2">
              <div>
                <dt className="mb-1 font-dm text-[11px] uppercase tracking-widest text-white/40">
                  First name
                </dt>
                <dd className="font-dm text-sm text-white/75">{user?.first_name ?? "—"}</dd>
              </div>
              <div>
                <dt className="mb-1 font-dm text-[11px] uppercase tracking-widest text-white/40">
                  Last name
                </dt>
                <dd className="font-dm text-sm text-white/75">{user?.last_name ?? "—"}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="mb-1 font-dm text-[11px] uppercase tracking-widest text-white/40">
                  User ID
                </dt>
                <dd className="break-all font-dm text-xs text-white/55">{user?.id ?? "—"}</dd>
              </div>
            </dl>
          </Card>

          <div className="space-y-6">
            <Card title="Organization" subtitle={org?.slug ? `@${org.slug}` : "Workspace details"}>
              <dl className="space-y-5">
                <div>
                  <dt className="mb-1 font-dm text-[11px] uppercase tracking-widest text-white/40">
                    Name
                  </dt>
                  <dd className="font-syne text-sm font-medium text-white/80">
                    {org?.name ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="mb-1 font-dm text-[11px] uppercase tracking-widest text-white/40">
                    Organization ID
                  </dt>
                  <dd className="break-all font-dm text-xs text-white/55">{org?.id ?? "—"}</dd>
                </div>
              </dl>
            </Card>

            <Card title="API keys" subtitle="Create and manage tenant keys">
              <p className="mb-4 font-dm text-sm leading-6 text-white/50">
                API keys are managed from each tenant. Open the tenant list to view its keys.
              </p>
              <Link
                href="/dashboard/tenants"
                className="inline-flex items-center gap-2 rounded-lg border border-brand/30 bg-brand/10 px-4 py-2 font-dm text-xs font-medium text-brand transition-colors hover:bg-brand/15"
              >
                Go to tenants <span aria-hidden="true">→</span>
              </Link>
            </Card>
          </div>
        </div>

        <Card title="Profile changes" subtitle="Editing profile details is not available yet">
          <p className="font-dm text-sm leading-6 text-white/50">
            Your account details are shown here for reference. Profile editing is not available from
            this screen yet.
          </p>
        </Card>
      </div>
    </DashboardShell>
  )
}
