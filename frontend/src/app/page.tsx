import Navbar from '@/components/Navbar'
import Hero from '@/components/Hero'

export default function HomePage() {
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
