import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface NavbarProps {
  variant?: 'transparent' | 'frosted';
  glassPill?: boolean;
}

function Navbar({ glassPill = false }: NavbarProps) {
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const isDashboard = location.pathname === '/';

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const containerClass = glassPill
    ? `fixed top-4 left-1/2 -translate-x-1/2 z-50 transition-all duration-500 ${
        scrolled || isDashboard
          ? 'bg-white/10 backdrop-blur-xl border border-white/20 shadow-lg shadow-black/20 rounded-full px-6 py-3'
          : 'bg-transparent'
      }`
    : `fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled || isDashboard
          ? 'bg-gradient-to-b from-gray-900/80 to-gray-900/40 backdrop-blur-xl border-b border-white/10'
          : 'bg-transparent'
      }`;

  return (
    <nav className={containerClass}>
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-14">
          <Link
            to="/"
            className="flex items-center gap-2 text-white font-semibold text-lg tracking-tight hover:opacity-80 transition-opacity"
          >
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-xs font-bold">
              V
            </div>
            Vortex
          </Link>

          <div className="flex items-center gap-1">
            <Link
              to="/"
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                location.pathname === '/'
                  ? 'bg-white/15 text-white'
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/team"
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                location.pathname === '/team'
                  ? 'bg-white/15 text-white'
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
            >
              Team
            </Link>
            <Link
              to="/settings"
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                location.pathname === '/settings'
                  ? 'bg-white/15 text-white'
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
            >
              Settings
            </Link>

            <div className="w-px h-5 bg-white/20 mx-2" />

            <button
              onClick={() => {
                localStorage.removeItem('access_token');
                window.location.href = '/login';
              }}
              className="px-4 py-1.5 rounded-full text-sm font-medium text-white/70 hover:text-white hover:bg-white/10 transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
