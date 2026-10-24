"use client"

import { useEffect, useState } from "react"
import AnalyticsTrendChart from "@/components/dashboard/AnalyticsTrendChart"
import DashboardShell from "@/components/dashboard/DashboardShell"
import Badge from "@/components/ui/Badge"
import Card from "@/components/ui/Card"
import EmptyState from "@/components/ui/EmptyState"
import Select from "@/components/ui/Select"
import Spinner from "@/components/ui/Spinner"
import StatCard from "@/components/ui/StatCard"
import { analyticsApi, orgApi, tenantApi } from "@/services/api.services"
import type {
  AnalyticsActiveUsersPoint,
  AnalyticsBreakdownValue,
  AnalyticsMetricComparison,
  AnalyticsOverview,
  AnalyticsRecentEvent,
  AnalyticsTimePoint,
  AnalyticsTopEvent,
  Organization,
  Tenant,
} from "@/services/api.types"

const ranges = [
  { days: 7, label: "7 days" },
  { days: 30, label: "30 days" },
  { days: 90, label: "90 days" },
]

const breakdownOptions = [
  { value: "url", label: "URL" },
  { value: "country", label: "Country" },
  { value: "browser", label: "Browser" },
  { value: "device_type", label: "Device type" },
  { value: "referrer", label: "Referrer" },
]

const countFormat = new Intl.NumberFormat(undefined, {
  notation: "compact",
  maximumFractionDigits: 1,
})

function comparisonTrend(metric?: AnalyticsMetricComparison) {
  if (!metric || metric.change_percent === null) return undefined
  return {
    value: Math.abs(metric.change_percent),
    positive: metric.change_percent >= 0,
  }
}

function formatDateTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date)
}

export default function DashboardPage() {
  const [org, setOrg] = useState<Organization | null>(null)
  const [memberCount, setMemberCount] = useState(0)
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [workspaceLoading, setWorkspaceLoading] = useState(true)

  const [rangeDays, setRangeDays] = useState(30)
  const [tenantId, setTenantId] = useState("")
  const [draftEventName, setDraftEventName] = useState("")
  const [eventName, setEventName] = useState("")
  const [breakdownProperty, setBreakdownProperty] = useState("url")
  const [timeseriesInterval, setTimeseriesInterval] = useState<"hour" | "day">("day")
  const [activeUsersInterval, setActiveUsersInterval] = useState<"day" | "week" | "month">("day")

  const [overview, setOverview] = useState<AnalyticsOverview | null>(null)
  const [timeseries, setTimeseries] = useState<AnalyticsTimePoint[]>([])
  const [topEvents, setTopEvents] = useState<AnalyticsTopEvent[]>([])
  const [breakdown, setBreakdown] = useState<AnalyticsBreakdownValue[]>([])
  const [activeUsers, setActiveUsers] = useState<AnalyticsActiveUsersPoint[]>([])
  const [recentEvents, setRecentEvents] = useState<AnalyticsRecentEvent[]>([])
  const [analyticsLoading, setAnalyticsLoading] = useState(true)
  const [analyticsError, setAnalyticsError] = useState(false)

  useEffect(() => {
    let cancelled = false

    const loadWorkspace = async () => {
      const [orgResult, membersResult, tenantsResult] = await Promise.allSettled([
        orgApi.getMe(),
        orgApi.getMembers({ limit: 50 }),
        tenantApi.listAll(),
      ])

      if (cancelled) return
      if (orgResult.status === "fulfilled" && orgResult.value?.data?.data) {
        setOrg(orgResult.value.data.data)
      }
      if (membersResult.status === "fulfilled" && membersResult.value?.data?.data) {
        setMemberCount(
          membersResult.value.data.meta?.total_count ?? membersResult.value.data.data.length
        )
      }
      if (tenantsResult.status === "fulfilled") {
        setTenants(tenantsResult.value)
      }
      setWorkspaceLoading(false)
    }

    void loadWorkspace()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    const loadAnalytics = async () => {
      setAnalyticsLoading(true)
      setAnalyticsError(false)

      const to = new Date()
      const from = new Date(to.getTime() - rangeDays * 24 * 60 * 60 * 1000)
      const filters = {
        from: from.toISOString(),
        to: to.toISOString(),
        ...(eventName ? { event_name: eventName } : {}),
        ...(tenantId ? { tenant_id: tenantId } : {}),
      }

      const results = await Promise.allSettled([
        analyticsApi.overview(filters),
        analyticsApi.timeseries(filters, timeseriesInterval),
        analyticsApi.topEvents(filters),
        analyticsApi.breakdown(filters, breakdownProperty),
        analyticsApi.activeUsers(filters, activeUsersInterval),
        analyticsApi.recentEvents(filters),
      ])

      if (cancelled) return

      const [
        overviewResult,
        timeseriesResult,
        topEventsResult,
        breakdownResult,
        usersResult,
        recentResult,
      ] = results
      setOverview(overviewResult.status === "fulfilled" ? overviewResult.value.data.data : null)
      setTimeseries(
        timeseriesResult.status === "fulfilled" ? (timeseriesResult.value.data.data ?? []) : []
      )
      setTopEvents(
        topEventsResult.status === "fulfilled" ? (topEventsResult.value.data.data ?? []) : []
      )
      setBreakdown(
        breakdownResult.status === "fulfilled" ? (breakdownResult.value.data.data ?? []) : []
      )
      setActiveUsers(usersResult.status === "fulfilled" ? (usersResult.value.data.data ?? []) : [])
      setRecentEvents(
        recentResult.status === "fulfilled" ? (recentResult.value.data.data ?? []) : []
      )
      setAnalyticsError(results.some((result) => result.status === "rejected"))
      setAnalyticsLoading(false)
    }

    void loadAnalytics()
    return () => {
      cancelled = true
    }
  }, [activeUsersInterval, breakdownProperty, eventName, rangeDays, tenantId, timeseriesInterval])

  const tenantOptions = [
    { value: "", label: "All organization tenants" },
    ...tenants.map((tenant) => ({
      value: tenant.id,
      label: `${tenant.tenant_name} · ${tenant.slug}`,
    })),
  ]

  const applyEventFilter = () => setEventName(draftEventName.trim())

  return (
    <DashboardShell
      title="Overview"
      subtitle={`Product activity${org?.name ? ` across ${org.name}` : " across your organization"}`}
    >
      <div className="space-y-6 2xl:space-y-8">
        <Card className="!p-0">
          <div className="grid grid-cols-1 gap-5 p-5 xl:grid-cols-[auto_minmax(220px,1fr)_minmax(220px,1.2fr)_auto] xl:items-end">
            <div>
              <p className="mb-2 font-dm text-[11px] uppercase tracking-[0.18em] text-white/40">
                Date range
              </p>
              <div className="flex rounded-lg border border-white/10 bg-white/[0.03] p-1">
                {ranges.map((range) => (
                  <button
                    key={range.days}
                    type="button"
                    onClick={() => setRangeDays(range.days)}
                    aria-pressed={rangeDays === range.days}
                    className={`rounded-md px-3 py-2 font-dm text-xs transition-colors sm:px-4 ${
                      rangeDays === range.days
                        ? "bg-brand/15 text-brand"
                        : "text-white/45 hover:text-white/80"
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
            </div>

            <Select
              id="analytics-tenant"
              label="Tenant"
              value={tenantId}
              onChange={setTenantId}
              options={tenantOptions}
            />

            <div>
              <label
                htmlFor="analytics-event-name"
                className="mb-2 block font-dm text-xs uppercase tracking-widest text-white/50"
              >
                Event name
              </label>
              <input
                id="analytics-event-name"
                value={draftEventName}
                onChange={(event) => setDraftEventName(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") applyEventFilter()
                }}
                placeholder="All events"
                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-dm text-sm text-white placeholder-white/25 transition-colors focus:border-brand/50 focus:outline-none focus:ring-1 focus:ring-brand/50"
              />
            </div>

            <button
              type="button"
              onClick={applyEventFilter}
              className="rounded-lg border border-brand/30 bg-brand/10 px-5 py-3 font-dm text-xs uppercase tracking-widest text-brand transition-colors hover:bg-brand/20 focus:outline-none focus:ring-2 focus:ring-brand/50"
            >
              Apply filters
            </button>
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-[var(--color-border)] px-5 py-3 font-dm text-[11px] text-white/35">
            <span>{tenantId ? "Tenant view" : "Organization view"}</span>
            {eventName && <Badge variant="info">{eventName}</Badge>}
            <span className="xl:ml-auto">Compared with the previous period of equal length</span>
          </div>
        </Card>

        {analyticsError && (
          <div
            role="status"
            className="rounded-lg border border-[var(--color-accent3)]/20 bg-[var(--color-accent3)]/5 px-4 py-3 font-dm text-sm text-[var(--color-accent3)]"
          >
            Some analytics panels could not load. The panels that loaded are still available; check
            your connection and try changing a filter to reload.
          </div>
        )}

        <section
          aria-label="Period summary"
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
        >
          <StatCard
            label="Events"
            value={
              overview
                ? countFormat.format(overview.total_events.current)
                : analyticsLoading
                  ? "…"
                  : "—"
            }
            trend={comparisonTrend(overview?.total_events)}
            className="h-full"
          />
          <StatCard
            label="Unique users"
            value={
              overview
                ? countFormat.format(overview.unique_users.current)
                : analyticsLoading
                  ? "…"
                  : "—"
            }
            trend={comparisonTrend(overview?.unique_users)}
            className="h-full"
          />
          <StatCard
            label="Sessions"
            value={
              overview
                ? countFormat.format(overview.sessions.current)
                : analyticsLoading
                  ? "…"
                  : "—"
            }
            trend={comparisonTrend(overview?.sessions)}
            className="h-full"
          />
          <StatCard
            label="Tenants"
            value={workspaceLoading ? "…" : tenants.length}
            className="h-full"
          />
        </section>
        <p className="-mt-4 px-1 font-dm text-[10px] text-white/30">
          Trend percentages compare each metric with the preceding date range.
        </p>

        <section aria-label="Event activity" className="grid grid-cols-1 gap-6 xl:grid-cols-12">
          <Card
            title="Events over time"
            subtitle="Volume by hour or day"
            className="min-w-0 xl:col-span-8"
            action={
              <Select
                id="timeseries-interval"
                value={timeseriesInterval}
                onChange={(value) => setTimeseriesInterval(value as "hour" | "day")}
                options={[
                  { value: "day", label: "Daily" },
                  { value: "hour", label: "Hourly" },
                ]}
                className="w-28"
              />
            }
          >
            {analyticsLoading && timeseries.length === 0 ? (
              <div className="flex h-56 items-center justify-center">
                <Spinner className="text-brand" />
              </div>
            ) : (
              <AnalyticsTrendChart
                rows={timeseries.map((point) => ({ bucket: point.bucket, value: point.count }))}
                valueLabel="events"
              />
            )}
          </Card>

          <Card
            title="Top events"
            subtitle="Most frequent event names in this period"
            className="min-w-0 xl:col-span-4"
          >
            {analyticsLoading && topEvents.length === 0 ? (
              <div className="flex h-56 items-center justify-center">
                <Spinner className="text-brand" />
              </div>
            ) : topEvents.length === 0 ? (
              <EmptyState
                title="No events yet"
                description="Events will appear here after they are received."
              />
            ) : (
              <div className="space-y-5">
                {topEvents.map((item, index) => {
                  const largest = Math.max(...topEvents.map((event) => event.count), 1)
                  const width = Math.max((item.count / largest) * 100, 2)
                  return (
                    <div key={item.event_name}>
                      <div className="mb-2 flex items-center justify-between gap-4">
                        <div className="flex min-w-0 items-center gap-2">
                          <span className="font-dm text-[10px] text-white/30">
                            {String(index + 1).padStart(2, "0")}
                          </span>
                          <span
                            className="truncate font-dm text-xs text-white/75"
                            title={item.event_name}
                          >
                            {item.event_name}
                          </span>
                        </div>
                        <span className="shrink-0 font-dm text-xs text-white/50">
                          {item.count.toLocaleString()}
                        </span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                        <div
                          className="h-full rounded-full bg-brand/80 transition-[width]"
                          style={{ width: `${width}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </section>

        <section
          aria-label="Audience and properties"
          className="grid grid-cols-1 gap-6 xl:grid-cols-12"
        >
          <Card
            title="Active users"
            subtitle="Distinct people active in each period"
            className="min-w-0 xl:col-span-7"
            action={
              <Select
                id="active-users-interval"
                value={activeUsersInterval}
                onChange={(value) => setActiveUsersInterval(value as "day" | "week" | "month")}
                options={[
                  { value: "day", label: "Daily" },
                  { value: "week", label: "Weekly" },
                  { value: "month", label: "Monthly" },
                ]}
                className="w-28"
              />
            }
          >
            {analyticsLoading && activeUsers.length === 0 ? (
              <div className="flex h-56 items-center justify-center">
                <Spinner className="text-brand" />
              </div>
            ) : (
              <AnalyticsTrendChart
                rows={activeUsers.map((point) => ({
                  bucket: point.bucket,
                  value: point.active_users,
                }))}
                valueLabel="active users"
                color="#7c6afa"
              />
            )}
          </Card>

          <Card
            title="Property breakdown"
            subtitle={`Event counts grouped by ${breakdownProperty.replaceAll("_", " ")}`}
            className="min-w-0 xl:col-span-5"
            action={
              <Select
                id="breakdown-property"
                value={breakdownProperty}
                onChange={setBreakdownProperty}
                options={breakdownOptions}
                className="w-32 sm:w-36"
              />
            }
          >
            {analyticsLoading && breakdown.length === 0 ? (
              <div className="flex h-56 items-center justify-center">
                <Spinner className="text-brand" />
              </div>
            ) : breakdown.length === 0 ? (
              <EmptyState
                title={`No ${breakdownProperty.replaceAll("_", " ")} values`}
                description="This property may not be present on events in the selected period."
              />
            ) : (
              <div className="space-y-4">
                {breakdown.map((item) => {
                  const largest = Math.max(...breakdown.map((value) => value.count), 1)
                  const width = Math.max((item.count / largest) * 100, 2)
                  return (
                    <div key={item.value}>
                      <div className="mb-2 flex items-center justify-between gap-4">
                        <span
                          className="min-w-0 truncate font-dm text-xs text-white/70"
                          title={item.value}
                        >
                          {item.value}
                        </span>
                        <span className="shrink-0 font-dm text-xs text-white/45">
                          {item.count.toLocaleString()}
                        </span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                        <div
                          className="h-full rounded-full bg-[var(--color-accent2)]/80"
                          style={{ width: `${width}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </section>

        <Card
          title="Recent events"
          subtitle="Latest events in the selected date range"
          action={
            <Badge variant="success" className="gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-current" />
              Latest
            </Badge>
          }
        >
          {analyticsLoading && recentEvents.length === 0 ? (
            <div className="flex h-40 items-center justify-center">
              <Spinner className="text-brand" />
            </div>
          ) : recentEvents.length === 0 ? (
            <EmptyState
              title="Waiting for your first event"
              description="Send an event with one of your tenant API keys. It will appear here once processed."
            />
          ) : (
            <div className="divide-y divide-[var(--color-border)]">
              {recentEvents.map((event) => {
                const properties = Object.entries(event.properties).slice(0, 3)
                return (
                  <article
                    key={event.id}
                    className="grid grid-cols-1 gap-2 py-4 first:pt-0 last:pb-0 lg:grid-cols-[minmax(160px,0.8fr)_minmax(150px,0.7fr)_minmax(220px,1.5fr)_auto] lg:items-center lg:gap-5"
                  >
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
                      <span
                        className="truncate font-dm text-sm text-white"
                        title={event.event_name}
                      >
                        {event.event_name}
                      </span>
                    </div>
                    <span
                      className="truncate font-dm text-xs text-white/45"
                      title={event.distinct_id}
                    >
                      {event.distinct_id}
                    </span>
                    <div className="flex min-w-0 flex-wrap gap-x-3 gap-y-1">
                      {properties.length > 0 ? (
                        properties.map(([key, value]) => (
                          <span
                            key={key}
                            className="max-w-full truncate font-dm text-[11px] text-white/35"
                          >
                            <span className="text-white/50">{key}:</span> {String(value)}
                          </span>
                        ))
                      ) : (
                        <span className="font-dm text-[11px] text-white/25">No properties</span>
                      )}
                    </div>
                    <time
                      dateTime={event.occurred_at}
                      className="font-dm text-[11px] text-white/35 lg:text-right"
                    >
                      {formatDateTime(event.occurred_at)}
                    </time>
                  </article>
                )
              })}
            </div>
          )}
        </Card>

        <Card
          title="Workspace"
          subtitle={org?.slug ? `@${org.slug}` : "Organization details"}
          action={
            <a
              href="/dashboard/tenants"
              className="font-dm text-xs text-brand transition-colors hover:text-brand-dark"
            >
              Manage tenants →
            </a>
          }
        >
          {workspaceLoading ? (
            <div className="flex justify-center py-4">
              <Spinner size="sm" className="text-brand" />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-5 sm:grid-cols-4">
              <div>
                <p className="font-dm text-[10px] uppercase tracking-widest text-white/35">
                  Organization
                </p>
                <p className="mt-1 truncate font-syne text-sm text-white/80" title={org?.name}>
                  {org?.name ?? "—"}
                </p>
              </div>
              <div>
                <p className="font-dm text-[10px] uppercase tracking-widest text-white/35">
                  Members
                </p>
                <p className="mt-1 font-syne text-sm text-white/80">{memberCount}</p>
              </div>
              <div>
                <p className="font-dm text-[10px] uppercase tracking-widest text-white/35">
                  Tenants
                </p>
                <p className="mt-1 font-syne text-sm text-white/80">{tenants.length}</p>
              </div>
              <div>
                <p className="font-dm text-[10px] uppercase tracking-widest text-white/35">
                  Created
                </p>
                <p className="mt-1 font-syne text-sm text-white/80">
                  {org?.created_at ? new Date(org.created_at).toLocaleDateString() : "—"}
                </p>
              </div>
            </div>
          )}
        </Card>
      </div>
    </DashboardShell>
  )
}
