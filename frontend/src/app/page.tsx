import Navbar from "@/components/Navbar"
import WorldMapDemo from "@/components/world-map-demo"

export default function HomePage() {
  return (
    <div className="relative bg-black min-h-screen">
      <Navbar />
      <WorldMapDemo />
    </div>
  )
}
