import { Outlet, useLocation } from 'react-router-dom';
import Navbar from '@app/layout/Navbar';
import Hero from '@components/Hero';

function RootLayout() {
  const location = useLocation();
  const isDashboard = location.pathname === '/';

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar
        variant={isDashboard ? 'frosted' : 'transparent'}
        glassPill={!isDashboard}
      />

      {isDashboard ? (
        <div className="pt-20 px-6">
          <Outlet />
        </div>
      ) : (
        <Hero>
          <div className="text-center z-10 px-4">
            <h1 className="text-6xl md:text-8xl font-bold text-white mb-4 tracking-tighter">
              Vortex
            </h1>
            <p className="text-xl text-white/70 mb-8 max-w-md mx-auto">
              Link intelligence, reimagined.
            </p>
            <a
              href="/login"
              className="inline-flex items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-full font-medium transition-all border border-white/20"
            >
              Get Started
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </a>
          </div>
        </Hero>
      )}
    </div>
  );
}

export default RootLayout;
