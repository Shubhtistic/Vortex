import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 50) {
        setIsScrolled(true)
      } else {
        setIsScrolled(false)
      }
    }

    window.addEventListener('scroll', handleScroll)
    return () => {
      window.removeEventListener('scroll', handleScroll)
    }
  }, [])

  const containerClasses = `mx-auto transition-all duration-300 max-w-5xl px-8 ${isScrolled ? 'bg-white/10 backdrop-blur-md rounded-full mt-4' : 'bg-transparent mt-0'}`

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 transition-all duration-300">
      <div className={containerClasses}>
        <div className="flex justify-between items-center py-4">
          <Link to="/" className="text-white text-xl font-bold">
            Vortex
          </Link>
          <div className="space-x-4">
            <Link to="/login" className="text-white hover:text-gray-200">
              Login
            </Link>
            <Link to="/signup" className="text-white hover:text-gray-200">
              Sign Up
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}
