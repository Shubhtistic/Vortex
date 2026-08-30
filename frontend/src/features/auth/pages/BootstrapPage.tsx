import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useBootstrap } from '../hooks'
import Button from '@components/Button'
import Input from '@components/Input'

function BootstrapPage() {
  const navigate = useNavigate()
  const bootstrapMutation = useBootstrap()
  const [tenantName, setTenantName] = React.useState('')
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const result = await bootstrapMutation.mutateAsync({
      tenant_name: tenantName,
      email,
      password,
    })
    if (result.access_token) {
      navigate('/')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Welcome to Vortex</h1>
        <p className="text-gray-500 mb-6">Create your account to get started</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Tenant Name"
            value={tenantName}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTenantName(e.target.value)}
            required
          />
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
            required
          />
          <Button type="submit" className="w-full" disabled={bootstrapMutation.isPending}>
            {bootstrapMutation.isPending ? 'Creating...' : 'Get Started'}
          </Button>
        </form>
      </div>
    </div>
  )
}

export default BootstrapPage
