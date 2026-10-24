"use client"

import { useEffect, useState } from "react"
import DashboardShell from "@/components/dashboard/DashboardShell"
import Badge from "@/components/ui/Badge"
import Button from "@/components/ui/Button"
import Card from "@/components/ui/Card"
import EmptyState from "@/components/ui/EmptyState"
import Input from "@/components/ui/Input"
import Modal from "@/components/ui/Modal"
import Select from "@/components/ui/Select"
import { orgApi } from "@/services/api.services"
import type { InviteMemberPayload, OrgMember } from "@/services/api.types"

export default function MembersPage() {
  const [members, setMembers] = useState<OrgMember[]>([])
  const [loading, setLoading] = useState(true)
  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviting, setInviting] = useState(false)
  const [inviteError, setInviteError] = useState("")
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [role, setRole] = useState("analyst")

  useEffect(() => {
    orgApi
      .getMembers({ limit: 50 })
      .then((res) => {
        if (res?.data?.data) setMembers(res.data.data)
      })
      .catch((err: unknown) => {
        const msg =
          err instanceof Error && "frontendMessage" in err
            ? (err as { frontendMessage: string }).frontendMessage
            : "Failed to load members"
        console.error(msg, err)
      })
      .finally(() => setLoading(false))
  }, [])

  const handleInvite = async () => {
    setInviteError("")
    if (!firstName || !lastName || !email || !password) {
      setInviteError("All fields are required")
      return
    }
    setInviting(true)
    try {
      const payload: InviteMemberPayload = {
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        role: role as "admin" | "analyst",
      }
      await orgApi.inviteMember(payload)
      setInviteOpen(false)
      setFirstName("")
      setLastName("")
      setEmail("")
      setPassword("")
      setRole("analyst")
      const res = await orgApi.getMembers({ limit: 50 })
      if (res?.data?.data) setMembers(res.data.data)
    } catch (err: unknown) {
      const message =
        err instanceof Error && "response" in err
          ? ((err as { response?: { data?: { message?: string } } }).response?.data?.message ??
            "Invite failed")
          : "Invite failed"
      setInviteError(message)
    } finally {
      setInviting(false)
    }
  }

  const handleDeactivate = async (member: OrgMember) => {
    if (!window.confirm(`Remove ${member.first_name} ${member.last_name} from the organization?`))
      return
    try {
      await orgApi.deactivateMember(member.user_id)
      setMembers((prev) => prev.filter((m) => m.user_id !== member.user_id))
    } catch {
      /* silent fail */
    }
  }

  if (loading) {
    return (
      <DashboardShell title="Members" subtitle="Loading members">
        <div className="flex min-h-40 items-center justify-center">
          <span className="font-dm text-sm uppercase tracking-widest text-white/60">
            Loading...
          </span>
        </div>
      </DashboardShell>
    )
  }

  return (
    <DashboardShell title="Members" subtitle={`${members.length} members`}>
      <div className="mb-8">
        <Button onClick={() => setInviteOpen(true)} size="sm">
          Invite Member
        </Button>
      </div>

      <Card>
        {members.length === 0 ? (
          <EmptyState
            title="No members yet"
            description="Invite your first team member to get started."
            action={
              <Button onClick={() => setInviteOpen(true)} size="sm">
                Invite Member
              </Button>
            }
          />
        ) : (
          <div className="space-y-3">
            {members.map((member) => (
              <div
                key={member.user_id}
                className="flex items-center justify-between py-3 border-b border-[var(--color-border)] last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-brand/10 border border-brand/20 flex items-center justify-center">
                    <span className="text-sm font-syne font-bold text-brand">
                      {member.first_name?.[0]}
                      {member.last_name?.[0]}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-white font-dm">
                      {member.first_name} {member.last_name}
                    </p>
                    <p className="text-xs text-white/40 font-dm">{member.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge
                    variant={
                      member.role === "owner"
                        ? "warning"
                        : member.role === "admin"
                          ? "info"
                          : "default"
                    }
                  >
                    {member.role}
                  </Badge>
                  {member.role !== "owner" && (
                    <Button variant="ghost" size="sm" onClick={() => handleDeactivate(member)}>
                      Remove
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Modal
        isOpen={inviteOpen}
        onClose={() => {
          setInviteOpen(false)
          setInviteError("")
        }}
        title="Invite Member"
        subtitle="Send an invitation to join your organization"
        footer={
          <>
            <Button variant="ghost" onClick={() => setInviteOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleInvite} disabled={inviting}>
              {inviting ? "Sending..." : "Send Invite"}
            </Button>
          </>
        }
      >
        {inviteError && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-dm">
            {inviteError}
          </div>
        )}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="First name"
              value={firstName}
              onChange={setFirstName}
              placeholder="Jane"
            />
            <Input label="Last name" value={lastName} onChange={setLastName} placeholder="Doe" />
          </div>
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="jane@company.com"
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            placeholder="Minimum 8 characters"
          />
          <Select
            label="Role"
            value={role}
            onChange={setRole}
            options={[
              { value: "analyst", label: "Analyst" },
              { value: "admin", label: "Admin" },
            ]}
          />
        </div>
      </Modal>
    </DashboardShell>
  )
}
