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
      navigate('/chat');
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
    <div className="min-h-screen relative overflow-hidden bg-black">
      <CosmicBackground />
      <div className="relative z-10 mx-auto flex max-w-4xl flex-col gap-12 px-6 py-12">
        <div className="grid gap-10 lg:grid-cols-[1fr,0.95fr]">
          <div className="flex flex-col gap-6 text-white">
            <span className="text-xs uppercase tracking-[0.5em] text-white/50">Seven planets</span>
            <h1 className="text-5xl font-semibold tracking-tight">NEUROASTRO</h1>
            <p className="text-sm text-white/60">
              Black, white, and precise—seven planetary paths guiding every tap.
            </p>
            <PlanetOrbit size="lg" className="pointer-events-none" />
          </div>

          <LiquidPanel className="space-y-6 px-8 py-10">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-1 text-xs uppercase tracking-[0.3em] text-white/50">Sign in</div>

              <div className="space-y-2">
                <label className="text-[0.65rem] uppercase tracking-[0.4em] text-white/40" htmlFor="email">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-2xl border border-white/15 bg-transparent px-4 py-3 text-sm text-white placeholder:text-white/35 focus:border-white focus:outline-none"
                  placeholder="cosmo@astro.com"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-[0.65rem] uppercase tracking-[0.4em] text-white/40" htmlFor="password">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-2xl border border-white/15 bg-transparent px-4 py-3 text-sm text-white placeholder:text-white/40 focus:border-white focus:outline-none"
                  placeholder="••••••••"
                  required
                />
              </div>

              {error && <div className="text-xs text-rose-300">{error}</div>}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-2xl border border-white/25 bg-white/80 py-3 text-sm font-semibold text-black transition hover:bg-white"
              >
                {loading ? 'Entering…' : 'Enter the cosmos'}
              </button>
            </form>

            <p className="text-center text-[0.6rem] uppercase tracking-[0.4em] text-white/40">
              <Link to="/signup" className="text-white">
                Create access
              </Link>
            </p>
          </LiquidPanel>
        </div>
      </div>
    </div>
  );
};
