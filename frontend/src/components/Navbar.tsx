"use client"

import Link from "next/link"
import { useEffect, useState } from "react"

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const pillClass = `mx-auto transition-all duration-300 max-w-5xl px-8 ${
    isScrolled ? "bg-white/10 backdrop-blur-md rounded-full mt-4" : "bg-transparent mt-0"
  }`

  return (
    <nav className="nav-fade fixed top-0 left-0 right-0 z-50">
      <div className={pillClass}>
        <div className="flex justify-between items-center py-4">
          <Link href="/" className="text-white text-xl font-bold font-syne tracking-tight">
            Vortex
          </Link>
          <div className="flex items-center space-x-4">
            <Link
              href="/login"
              className="text-white/80 hover:text-white transition-colors duration-200"
            >
              Login
            </Link>
            <Link
              href="/signup"
              className="text-white/80 hover:text-white transition-colors duration-200"
            >
              Sign Up
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}
