import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/auth/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL}/auth/:path*`,
      },
      {
        source: "/organizations/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL}/organizations/:path*`,
      },
    ]
  },
}

export default nextConfig
