import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AxiosError } from 'axios';

import { useAuth } from '@/contexts/useAuth';
import { CosmicBackground } from '@/components/CosmicBackground';
import { LiquidPanel } from '@/components/LiquidPanel';
import { PlanetOrbit } from '@/components/PlanetOrbit';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/birth-details');
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.data?.error) {
        setError(err.response.data.error);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black">
      <CosmicBackground />
      <div className="relative z-10 min-h-screen flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-2xl">
          {/* Top Section - Branding with Animation */}
          <div className="flex flex-col gap-6 sm:gap-8 text-white text-center mb-12 sm:mb-16 animate-fade-in">
            <div className="space-y-3 sm:space-y-4">
              <span className="text-xs uppercase tracking-[0.5em] text-white/50 inline-block">
                Seven planets
              </span>
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight bg-gradient-to-r from-white via-white/90 to-white/70 bg-clip-text text-transparent animate-slide-down">
                NEUROASTRO
              </h1>
              <p className="text-sm sm:text-base text-white/60 max-w-md mx-auto animate-slide-up">
                Black, white, and precise—seven planetary paths guiding every tap.
              </p>
            </div>

            {/* Planet Orbit Animation */}
            <div className="flex justify-center animate-bounce-slow">
              <PlanetOrbit size="lg" className="pointer-events-none" />
            </div>
          </div>

          {/* Credential Box - Animated Slide Up */}
          <div className="animate-slide-up-delayed">
            <LiquidPanel className="space-y-6 sm:space-y-8 px-6 sm:px-8 lg:px-10 py-8 sm:py-10 lg:py-12">
              <form onSubmit={handleSubmit} className="space-y-6 sm:space-y-7">
                {/* Form Header */}
                <div className="space-y-2 pb-4 sm:pb-6 border-b border-white/10">
                  <h2 className="text-lg sm:text-xl font-semibold text-white">Welcome Back</h2>
                  <p className="text-xs sm:text-sm text-white/50">Sign in to your cosmic account</p>
                </div>

                {/* Email Field */}
                <div className="space-y-2.5 group">
                  <label className="text-xs uppercase tracking-[0.3em] text-white/50 font-medium" htmlFor="email">
                    Email Address
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded-xl sm:rounded-2xl border border-white/15 bg-white/5 px-4 sm:px-5 py-3 sm:py-4 text-sm sm:text-base text-white placeholder:text-white/35 focus:bg-white/10 focus:border-white/40 focus:outline-none transition-all duration-200 group-hover:border-white/25"
                    placeholder="cosmo@astro.com"
                    required
                  />
                </div>

                {/* Password Field */}
                <div className="space-y-2.5 group">
                  <label className="text-xs uppercase tracking-[0.3em] text-white/50 font-medium" htmlFor="password">
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-xl sm:rounded-2xl border border-white/15 bg-white/5 px-4 sm:px-5 py-3 sm:py-4 text-sm sm:text-base text-white placeholder:text-white/40 focus:bg-white/10 focus:border-white/40 focus:outline-none transition-all duration-200 group-hover:border-white/25"
                    placeholder="••••••••"
                    required
                  />
                </div>

                {/* Error Message */}
                {error && (
                  <div className="rounded-lg bg-rose-500/15 border border-rose-500/30 px-4 py-3 text-sm text-rose-200 animate-shake">
                    {error}
                  </div>
                )}

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-xl sm:rounded-2xl bg-gradient-to-r from-white to-white/90 py-3 sm:py-4 text-sm sm:text-base font-semibold text-black transition-all duration-300 hover:from-white hover:to-white hover:shadow-lg hover:shadow-white/20 active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed transform hover:scale-105"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-black border-t-transparent"></span>
                      Entering…
                    </span>
                  ) : (
                    'Enter the cosmos'
                  )}
                </button>
              </form>

              {/* Signup Link */}
              <div className="pt-2 sm:pt-4 border-t border-white/10">
                <p className="text-center text-xs sm:text-sm text-white/60">
                  Don't have an account?{' '}
                  <Link to="/signup" className="font-semibold text-white hover:text-white/80 transition-colors hover:underline">
                    Create one
                  </Link>
                </p>
              </div>
            </LiquidPanel>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        @keyframes slide-down {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes slide-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes bounce-slow {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-10px);
          }
        }
        @keyframes shake {
          0%, 100% {
            transform: translateX(0);
          }
          25% {
            transform: translateX(-5px);
          }
          75% {
            transform: translateX(5px);
          }
        }
        .animate-fade-in {
          animation: fade-in 0.6s ease-out;
        }
        .animate-slide-down {
          animation: slide-down 0.7s ease-out;
        }
        .animate-slide-up {
          animation: slide-up 0.6s ease-out;
        }
        .animate-slide-up-delayed {
          animation: slide-up 0.7s ease-out 0.2s both;
        }
        .animate-bounce-slow {
          animation: bounce-slow 3s ease-in-out infinite;
        }
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
      `}</style>
    </div>
  );
};
