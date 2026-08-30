import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Vortex',
  description: 'Next-gen event tracking',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
