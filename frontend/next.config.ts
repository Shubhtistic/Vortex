import type { NextConfig } from 'next'

const backendApiUrl = process.env.BACKEND_API_URL?.replace(/\/+$/, '')

if (!backendApiUrl) {
  throw new Error('BACKEND_API_URL is not set. Configure it in .env.local or your deployment environment.')
}

const apiPrefixes = ['auth', 'organizations', 'users', 'tenants', 'analytics', 'events']

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return apiPrefixes.map((prefix) => ({
      source: `/${prefix}/:path*`,
      destination: `${backendApiUrl}/${prefix}/:path*`,
    }))
  },
}

export default nextConfig
