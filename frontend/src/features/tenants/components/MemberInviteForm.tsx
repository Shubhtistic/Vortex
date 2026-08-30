import { useState } from 'react'
import Button from '@components/Button'
import Input from '@components/Input'

interface MemberInviteFormProps {
  onInvite: (email: string, role: 'admin' | 'member') => Promise<void>
}

export function MemberInviteForm({ onInvite }: MemberInviteFormProps) {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<'admin' | 'member'>('member')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    await onInvite(email, role)
    setEmail('')
    setIsSubmitting(false)
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-4">
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
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Sending...' : 'Invite'}
      </Button>
    </form>
  )
}
