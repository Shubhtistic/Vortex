import React, { type ChangeEvent, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLogin } from '../hooks'
import Button from '@components/Button'
import Input from '@components/Input'

function LoginPage() {
  const navigate = useNavigate()
  const loginMutation = useLogin()
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const result = await loginMutation.mutateAsync({ email, password })
    if (result.access_token) {
      navigate('/')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">Sign in to Vortex</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
            required
          />
          <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage
