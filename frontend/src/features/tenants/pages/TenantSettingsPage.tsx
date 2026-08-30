import { useState } from 'react'
import { useTenantSettings, useInviteMember } from '../hooks'
import Button from '@components/Button'
import Input from '@components/Input'

function TenantSettingsPage() {
  const { data: tenant } = useTenantSettings()
  const inviteMutation = useInviteMember()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<'admin' | 'member'>('member')

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault()
    await inviteMutation.mutateAsync({ email, role })
    setEmail('')
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Tenant Settings</h2>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Organization</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name
            </label>
            <p className="text-gray-800">{tenant?.name ?? 'Loading...'}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Slug
            </label>
            <p className="text-gray-800">{tenant?.slug ?? 'Loading...'}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Plan
            </label>
            <p className="text-gray-800">{tenant?.plan ?? 'Loading...'}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Invite Member</h3>
        <form onSubmit={handleInvite} className="flex gap-4">
          <Input
            value={email}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
            placeholder="Email address"
            required
            className="flex-1"
          />
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as 'admin' | 'member')}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="member">Member</option>
            <option value="admin">Admin</option>
          </select>
          <Button type="submit" disabled={inviteMutation.isPending}>
            {inviteMutation.isPending ? 'Sending...' : 'Invite'}
          </Button>
        </form>
      </div>
    </div>
  )
}

export default TenantSettingsPage
