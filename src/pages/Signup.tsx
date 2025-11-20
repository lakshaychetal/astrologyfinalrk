import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '@/contexts/AuthContext';
import { CosmicBackground } from '@/components/CosmicBackground';
import { LiquidPanel } from '@/components/LiquidPanel';
import { PlanetOrbit } from '@/components/PlanetOrbit';

export const Signup = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await signup(email, password, name);
      navigate('/chat');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-black text-white">
      <CosmicBackground />
      <div className="relative z-10 mx-auto flex max-w-4xl flex-col gap-10 px-6 py-12">
        <div className="flex flex-col gap-3">
          <span className="text-xs uppercase tracking-[0.5em] text-white/50">Seven planets</span>
          <h1 className="text-5xl font-semibold tracking-tight">Begin the orbit</h1>
          <p className="text-sm text-white/60">A calm, monochrome gateway to the NeuroAstro universe.</p>
          <PlanetOrbit size="md" className="pointer-events-none" />
        </div>

        <LiquidPanel className="space-y-6 px-8 py-10">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-[0.65rem] uppercase tracking-[0.4em] text-white/40" htmlFor="name">
                Name
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-2xl border border-white/15 bg-transparent px-4 py-3 text-sm text-white placeholder:text-white/35 focus:border-white focus:outline-none"
                placeholder="Cosmic name"
                required
              />
            </div>
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
              {loading ? 'Opening…' : 'Create access'}
            </button>
          </form>

          <p className="text-center text-[0.6rem] uppercase tracking-[0.4em] text-white/40">
            Already have a passage?{' '}
            <Link to="/login" className="text-white">
              Sign in
            </Link>
          </p>
        </LiquidPanel>
      </div>
    </div>
  );
};
