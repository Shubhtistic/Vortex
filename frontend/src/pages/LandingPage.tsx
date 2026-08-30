import Hero from '@components/Hero'
import Navbar from '@app/layout/Navbar'

export default function LandingPage() {
  return (
    <div className="relative">
      <Navbar />
      <Hero />
      <div className="h-screen flex items-center justify-center">
        <h2 className="text-4xl">Content Section</h2>
      </div>
    </div>
  )
}
