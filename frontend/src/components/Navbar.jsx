import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Compass,
  MapPin,
  Calendar,
  Sparkles,
  BarChart3,
  FileText,
  User as UserIcon,
  LogOut,
  LogIn,
  Menu,
  X,
  Map as MapIcon,
  LayoutDashboard,
  Server,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ healthState }) {
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  const { status, latency } = healthState || { status: 'success' };

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Plan Trip', path: '/plan', icon: Calendar },
    { name: 'Attractions', path: '/recommendations', icon: MapPin },
    { name: 'Itinerary', path: '/itinerary', icon: Calendar },
    { name: 'Map', path: '/map', icon: MapIcon },
    { name: 'AI Assistant', path: '/assistant', icon: Sparkles, badge: 'AI' },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Reports', path: '/reports', icon: FileText },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header
      className={`sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-[#DCE6E3] transition-shadow duration-200 ${
        scrolled ? 'shadow-soft' : 'shadow-none'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <Link to="/" className="flex items-center space-x-3 group flex-shrink-0">
          <div className="w-10 h-10 rounded-xl bg-[#163B46] flex items-center justify-center shadow-soft group-hover:bg-[#244F59] transition-colors">
            <Compass className="w-5 h-5 text-[#18B8A6]" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center space-x-1">
              <span className="text-xl font-extrabold text-[#163B46] tracking-tight">
                TravelSense<span className="text-[#18B8A6]">AI</span>
              </span>
            </div>
            <span className="text-[10px] text-[#829196] tracking-wider font-semibold uppercase">
              Smart Travel Planner
            </span>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center space-x-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.path);
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`relative px-3 py-1.5 rounded-xl text-xs font-medium transition-all flex items-center space-x-1.5 ${
                  active
                    ? 'text-[#18B8A6] bg-[#18B8A6]/10 border border-[#18B8A6]/20 font-semibold'
                    : 'text-[#52636A] hover:text-[#163B46] hover:bg-[#EEF3F1]'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${active ? 'text-[#18B8A6]' : 'text-[#829196]'}`} />
                <span>{link.name}</span>
                {link.badge && (
                  <span className="px-1.5 py-0.2 rounded-full bg-[#18B8A6] text-[9px] font-bold text-white leading-none">
                    {link.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Right Section: API Health Pill & User / Auth Actions */}
        <div className="hidden sm:flex items-center space-x-3">
          {/* API Status Indicator */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-[#EEF3F1] border border-[#DCE6E3] text-[11px] font-medium text-[#52636A]">
            <Server className="w-3 h-3 text-[#829196]" />
            {status === 'loading' && (
              <span className="flex items-center text-[#E6A23C]">
                <RefreshCw className="w-2.5 h-2.5 animate-spin mr-1" />
                API Check
              </span>
            )}
            {status === 'success' && (
              <span className="flex items-center text-[#16A36A]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16A36A] animate-pulse mr-1" />
                API Online {latency ? `(${latency}ms)` : ''}
              </span>
            )}
            {status === 'error' && (
              <span className="flex items-center text-[#DC5555]">
                <AlertCircle className="w-2.5 h-2.5 mr-1" />
                API Offline
              </span>
            )}
          </div>

          {/* User Controls */}
          {isAuthenticated ? (
            <div className="flex items-center space-x-2">
              <Link
                to="/profile"
                className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-white border border-[#DCE6E3] hover:border-[#18B8A6] text-xs font-medium text-[#163B46] shadow-soft transition-all"
              >
                <UserIcon className="w-3.5 h-3.5 text-[#18B8A6]" />
                <span className="max-w-[120px] truncate">{user?.full_name || 'My Profile'}</span>
              </Link>
              <button
                onClick={handleLogout}
                title="Log out"
                className="p-1.5 rounded-xl bg-white border border-[#DCE6E3] text-[#829196] hover:text-[#DC5555] hover:border-[#DC5555]/30 transition-colors shadow-soft"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Link
                to="/login"
                className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-[#163B46] hover:bg-[#EEF3F1] transition-colors flex items-center space-x-1"
              >
                <LogIn className="w-3.5 h-3.5 mr-1 text-[#52636A]" />
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-4 py-1.5 rounded-xl text-xs font-semibold bg-[#18B8A6] hover:bg-[#129889] text-white shadow-soft transition-all hover:scale-[1.02]"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>

        {/* Mobile Menu Toggle Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-2 rounded-xl bg-[#EEF3F1] border border-[#DCE6E3] text-[#163B46] hover:bg-white"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-white border-b border-[#DCE6E3] px-4 pt-3 pb-6 space-y-3 shadow-soft-lg animate-in slide-in-from-top-2 duration-150">
          <div className="grid grid-cols-2 gap-2">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const active = isActive(link.path);
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`px-3 py-2.5 rounded-xl text-xs font-medium flex items-center space-x-2 transition-colors ${
                    active
                      ? 'bg-[#18B8A6]/10 text-[#18B8A6] border border-[#18B8A6]/20 font-semibold'
                      : 'text-[#52636A] bg-[#F4F7F6] hover:bg-[#EEF3F1] hover:text-[#163B46]'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-[#18B8A6]' : 'text-[#829196]'}`} />
                  <span>{link.name}</span>
                </Link>
              );
            })}
          </div>

          <div className="pt-3 border-t border-[#DCE6E3] flex flex-col space-y-2">
            {/* Mobile API Health Pill */}
            <div className="flex items-center justify-between px-3 py-2 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] text-xs text-[#52636A]">
              <span className="flex items-center space-x-1.5">
                <Server className="w-3.5 h-3.5 text-[#829196]" />
                <span>API Status</span>
              </span>
              <span className={`font-semibold ${status === 'success' ? 'text-[#16A36A]' : status === 'loading' ? 'text-[#E6A23C]' : 'text-[#DC5555]'}`}>
                {status === 'success' ? `Online (${latency || 15}ms)` : status === 'loading' ? 'Checking...' : 'Offline'}
              </span>
            </div>

            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full py-2.5 px-3 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] text-xs font-medium text-[#163B46] flex items-center justify-between"
                >
                  <span className="flex items-center space-x-2">
                    <UserIcon className="w-4 h-4 text-[#18B8A6]" />
                    <span>{user?.full_name}</span>
                  </span>
                  <span className="text-[10px] text-[#829196]">Profile</span>
                </Link>
                <button
                  onClick={() => {
                    handleLogout();
                    setMobileMenuOpen(false);
                  }}
                  className="w-full py-2.5 px-3 rounded-xl bg-red-50 text-[#DC5555] border border-red-200 text-xs font-medium flex items-center justify-center space-x-1.5"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Log Out</span>
                </button>
              </>
            ) : (
              <div className="grid grid-cols-2 gap-2 pt-1">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="py-2.5 px-3 text-center rounded-xl bg-white border border-[#DCE6E3] text-xs font-semibold text-[#163B46] hover:bg-[#EEF3F1]"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="py-2.5 px-3 text-center rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white text-xs font-bold shadow-soft"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
