import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Compass, Mail, Lock, Eye, EyeOff, LogIn, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ErrorMessage from '../components/ErrorMessage';
import LoadingSpinner from '../components/LoadingSpinner';

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // If already logged in, redirect
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError('Please provide both email and password.');
      return;
    }

    setLoading(true);
    try {
      await login({ email: email.trim(), password });
      const redirectTo = location.state?.from?.pathname || '/dashboard';
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <Link to="/" className="inline-flex items-center space-x-2.5">
            <div className="w-10 h-10 rounded-xl bg-[#163B46] flex items-center justify-center shadow-soft">
              <Compass className="w-6 h-6 text-[#18B8A6]" />
            </div>
            <span className="text-2xl font-extrabold text-[#163B46] tracking-tight">
              TravelSense<span className="text-[#18B8A6]">AI</span>
            </span>
          </Link>
          <h2 className="text-xl font-bold text-[#163B46]">Welcome Back</h2>
          <p className="text-xs sm:text-sm text-[#52636A]">
            Sign in to access your saved itineraries, custom preferences, and travel dashboard.
          </p>
        </div>

        {/* Card */}
        <div className="p-8 rounded-3xl bg-white border border-[#DCE6E3] shadow-soft">
          {error && (
            <div className="mb-6">
              <ErrorMessage message={error} title="Sign In Error" />
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#163B46]">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#829196] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white focus:ring-2 focus:ring-[#18B8A6]/20 text-xs sm:text-sm text-[#26383D] placeholder-[#829196] focus:outline-none transition-all"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-[#163B46]">Password</label>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#829196] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] focus:border-[#18B8A6] focus:bg-white focus:ring-2 focus:ring-[#18B8A6]/20 text-xs sm:text-sm text-[#26383D] placeholder-[#829196] focus:outline-none transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#829196] hover:text-[#163B46]"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-xs sm:text-sm shadow-soft transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              {loading ? (
                <LoadingSpinner size="sm" label="" />
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Sign In to Account</span>
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Hint */}
          <div className="mt-6 pt-5 border-t border-[#DCE6E3] text-center">
            <p className="text-xs text-[#52636A]">
              Don't have an account?{' '}
              <Link to="/register" className="text-[#18B8A6] hover:underline font-semibold">
                Register now
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
