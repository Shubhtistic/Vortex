import Link from 'next/link'

export default function SignupPage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
      <div className="max-w-md w-full p-8 border border-white/10 rounded-2xl bg-white/5">
        <h1 className="text-3xl font-bold mb-6">Sign Up</h1>
        <p className="text-white/60">Sign up page coming soon.</p>
        <Link href="/" className="block mt-6 text-cyan-400 hover:text-cyan-300">
          ← Back to home
        </Link>
      </div>
    </main>
  )
}
