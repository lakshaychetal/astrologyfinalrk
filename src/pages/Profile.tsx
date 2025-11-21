import { useAuth } from '@/contexts/useAuth';
import { CosmicBackground } from '@/components/CosmicBackground';
import { LiquidPanel } from '@/components/LiquidPanel';
import { PlanetOrbit } from '@/components/PlanetOrbit';
import { ArrowLeft, Mail, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Profile = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen relative overflow-hidden bg-black text-white">
      <CosmicBackground />
      <div className="relative z-10 mx-auto flex max-w-4xl flex-col gap-8 px-6 py-12">
        <div className="flex flex-col gap-3">
          <span className="text-xs uppercase tracking-[0.5em] text-white/50">Seven planets</span>
          <div className="flex items-center gap-3">
            <h1 className="text-4xl font-semibold tracking-tight">Profile</h1>
            <PlanetOrbit size="sm" className="pointer-events-none" />
          </div>
          <p className="text-sm text-white/60">Your minimal cosmic identity.</p>
        </div>

        <button
          onClick={() => navigate('/chat')}
          className="flex items-center gap-2 text-[0.6rem] uppercase tracking-[0.4em] text-white/60"
        >
          <ArrowLeft className="h-3 w-3" />
          Back to chat
        </button>

        <LiquidPanel className="space-y-6 px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[0.65rem] uppercase tracking-[0.4em] text-white/40">Cosmic traveler</p>
              <h2 className="text-3xl font-semibold">{user?.name || 'Guest'}</h2>
            </div>
            <div className="flex flex-col items-end text-xs text-white/50">
              <span className="tracking-[0.35em]">Orbit</span>
              <span className="text-[0.6rem] tracking-[0.35em]">{user?.id || '—'}</span>
            </div>
          </div>
          <div className="space-y-4">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3 text-sm text-white/60">
                <User className="h-4 w-4" />
                <span>Name</span>
              </div>
              <p className="mt-2 text-2xl font-semibold text-white">{user?.name || '—'}</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3 text-sm text-white/60">
                <Mail className="h-4 w-4" />
                <span>Email</span>
              </div>
              <p className="mt-2 text-lg font-semibold text-white/80">{user?.email || '—'}</p>
            </div>
          </div>
        </LiquidPanel>

        <LiquidPanel className="space-y-4 px-6 py-6">
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">Centered</p>
          <p className="text-sm text-white/60">Seven planets, one quiet orbit around your story.</p>
        </LiquidPanel>
      </div>
    </div>
  );
};
