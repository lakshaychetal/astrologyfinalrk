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
      <div className="relative z-10 mx-auto flex max-w-6xl flex-col gap-8 sm:gap-10 px-5 sm:px-8 lg:px-12 py-10 sm:py-14">
        <div className="flex flex-col gap-4">
          <span className="text-xs uppercase tracking-[0.5em] text-white/50">Seven planets</span>
          <div className="flex items-center gap-4">
            <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight">Profile</h1>
            <PlanetOrbit size="sm" className="pointer-events-none" />
          </div>
          <p className="text-base sm:text-lg text-white/60">Your minimal cosmic identity.</p>
        </div>

        <button
          onClick={() => navigate('/chat')}
          className="flex items-center gap-2 text-[0.65rem] uppercase tracking-[0.4em] text-white/60 hover:text-white transition-colors duration-300 w-fit"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to chat
        </button>

        <LiquidPanel className="space-y-7 px-6 sm:px-8 py-7 sm:py-10">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 pb-5 border-b border-white/5">
            <div>
              <p className="text-[0.7rem] uppercase tracking-[0.4em] text-white/40 mb-2">Cosmic traveler</p>
              <h2 className="text-3xl sm:text-4xl font-semibold break-words">{user?.name || 'Guest'}</h2>
            </div>
            <div className="flex flex-col items-start sm:items-end text-sm text-white/50">
              <span className="tracking-[0.35em]">Orbit</span>
              <span className="text-[0.65rem] tracking-[0.35em] break-all">{user?.id || '—'}</span>
            </div>
          </div>
          <div className="space-y-4 sm:space-y-5">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5 sm:p-7">
              <div className="flex items-center gap-3 text-base text-white/60 mb-3">
                <User className="h-5 w-5" />
                <span>Name</span>
              </div>
              <p className="text-2xl sm:text-3xl font-semibold text-white break-words">{user?.name || '—'}</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5 sm:p-7">
              <div className="flex items-center gap-3 text-base text-white/60 mb-3">
                <Mail className="h-5 w-5" />
                <span>Email</span>
              </div>
              <p className="text-lg sm:text-xl font-semibold text-white/80 break-all">{user?.email || '—'}</p>
            </div>
          </div>
        </LiquidPanel>

        <LiquidPanel className="space-y-5 px-6 sm:px-8 py-6 sm:py-8">
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">Centered</p>
          <p className="text-sm text-white/60">Seven planets, one quiet orbit around your story.</p>
        </LiquidPanel>
      </div>
    </div>
  );
};
