"use client"

import WorldMap from "@/components/ui/world-map"

export default function WorldMapDemo() {
  return (
    <div className="relative w-full bg-black overflow-hidden">
      {/* Top fade */}
      <div className="absolute top-0 left-0 right-0 h-40 pointer-events-none bg-gradient-to-b from-black via-black/90 to-transparent z-20" />
      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-40 pointer-events-none bg-gradient-to-t from-black via-black/90 to-transparent z-20" />

      <div className="map-fade relative z-10 min-h-screen flex flex-col items-center justify-center px-4 py-24">
        <div className="w-full max-w-6xl">
          <WorldMap
            dots={[
              {
                start: { lat: 78.5074, lng: 190.1278, label: "Arctic Ocean, north of the Chukchi Sea" },
                end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
              },
              {
                start: { lat: -80.2008, lng: 250.4937, label: "Antarctica, Marie Byrd Land region" },
                end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
              },
              {
                start: { lat: 64.2008, lng: -149.4937, label: "Interior Alaska, United States" },
                end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
              },
              {
                start: { lat: -88.2008, lng: -110.4937, label: "Antarctica, near the South Pole" },
                end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
              },
              {
                start: { lat: 120.2008, lng: -89.4937, label: "No real-world location: latitude exceeds 90° N" },
                end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
              },
              {
                start: { lat: -75.2008, lng: 88.4937, label: "East Antarctica, inland ice sheet" },
                end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
              },
              {
                start: { lat: 400.2008, lng: 270.4937, label: "No real-world location: latitude exceeds 90° N" },
                end: { lat: 4.7975, lng: 3.8919, label: "Gulf of Guinea" },
              },
            ]}
          />
        </div>
      </div>
    </div>
  )
}
