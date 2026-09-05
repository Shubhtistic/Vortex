'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import ThemeToggle from './theme-toggle'

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }

    window.addEventListener('scroll', handleScroll)
    return () => {
      window.removeEventListener('scroll', handleScroll)
    }
  }, [])

  const containerClasses = `mx-auto transition-all duration-300 max-w-5xl px-8 ${
    isScrolled
      ? 'bg-white/10 dark:bg-white/10 backdrop-blur-md rounded-full mt-4'
      : 'bg-transparent mt-0'
  }`

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 transition-all duration-300">
      <div className={containerClasses}>
        <div className="flex justify-between items-center py-4">
          <Link
            href="/"
            className="dark:text-white text-neutral-900 text-xl font-bold"
          >
            Vortex
          </Link>
          <div className="flex items-center space-x-4">
            <Link
              href="/login"
              className="dark:text-white text-neutral-700 dark:hover:text-gray-200 hover:text-neutral-500"
            >
              Login
            </Link>
            <Link
              href="/signup"
              className="dark:text-white text-neutral-700 dark:hover:text-gray-200 hover:text-neutral-500"
            >
              Sign Up
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </nav>
  )
}