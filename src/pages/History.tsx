import { useState, useEffect } from 'react';
import { chat } from '@/lib/api';
import { CosmicBackground } from '@/components/CosmicBackground';
import { LiquidPanel } from '@/components/LiquidPanel';
import { PlanetOrbit } from '@/components/PlanetOrbit';
import { ArrowLeft, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface ChatHistory {
  id: string;
  question: string;
  answer: string;
  niche: string;
  created_at: string;
}

export const History = () => {
  const [history, setHistory] = useState<ChatHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    chat
      .getHistory()
      .then((res) => setHistory(res.data.history || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen relative overflow-hidden bg-black text-white">
      <CosmicBackground />
      <div className="relative z-10 mx-auto flex max-w-5xl flex-col gap-8 px-6 py-10">
        <div className="flex flex-col gap-3">
          <span className="text-xs uppercase tracking-[0.5em] text-white/50">Seven planets</span>
          <div className="flex items-center gap-3">
            <h1 className="text-4xl font-semibold tracking-tight">Archive</h1>
            <PlanetOrbit size="sm" className="pointer-events-none" />
          </div>
          <p className="text-sm text-white/60">A calm ledger of every exchange.</p>
        </div>

        <button
          onClick={() => navigate('/chat')}
          className="flex items-center gap-2 text-[0.6rem] uppercase tracking-[0.4em] text-white/60"
        >
          <ArrowLeft className="h-3 w-3" />
          Back to chat
        </button>

        <LiquidPanel className="space-y-3 px-6 py-8">
          <div className="flex items-center gap-3 text-sm text-white/60">
            <Clock className="h-4 w-4" />
            <span>Every session is preserved, no extra noise.</span>
          </div>
          {history.length === 0 && !loading ? (
            <p className="text-xs uppercase tracking-[0.4em] text-white/40">Nothing archived yet.</p>
          ) : (
            <div className="flex flex-wrap gap-3 text-[0.6rem] uppercase tracking-[0.3em] text-white/40">
              <span className="liquid-tag">Curated</span>
              <span className="liquid-tag">Minimal</span>
            </div>
          )}
        </LiquidPanel>

        <div className="space-y-4">
          {loading ? (
            <div className="flex items-center justify-center">
              <div className="h-10 w-10 animate-spin rounded-full border-4 border-white/20 border-t-white" />
            </div>
          ) : history.length === 0 ? (
            <div className="rounded-3xl border border-white/10 bg-white/5 p-6 text-center text-sm text-white/60">
              No history yet. Ask a question to begin the archive.
            </div>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                className="rounded-3xl border border-white/10 bg-white/5 p-6 text-sm text-white/70"
              >
                <div className="flex items-center justify-between text-xs uppercase tracking-[0.4em] text-white/50">
                  <span>{item.niche}</span>
                  <span className="flex items-center gap-1 text-white/60">
                    <Clock className="h-3 w-3" />
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="mt-4 space-y-3">
                  <div>
                    <p className="text-[0.6rem] uppercase tracking-[0.4em] text-white/40">Question</p>
                    <p className="text-base text-white">{item.question}</p>
                  </div>
                  <div>
                    <p className="text-[0.6rem] uppercase tracking-[0.4em] text-white/40">Answer</p>
                    <p className="text-base text-white/80">{item.answer}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
