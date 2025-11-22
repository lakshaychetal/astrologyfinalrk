import { useState, useEffect } from 'react';
import { chat } from '@/lib/api';
import { CosmicBackground } from '@/components/CosmicBackground';
import { LiquidPanel } from '@/components/LiquidPanel';
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
      <div className="relative z-10 mx-auto flex max-w-7xl flex-col gap-8 sm:gap-10 px-5 sm:px-8 lg:px-12 py-10 sm:py-14">
        <div className="flex flex-col gap-4">
          <span className="text-xs uppercase tracking-[0.5em] text-white/50">Seven planets</span>
          <div className="flex items-center gap-4">
            <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight">Archive</h1>
            {/* <PlanetOrbit size="sm" className="pointer-events-none" /> */}
          </div>
          <p className="text-base sm:text-lg text-white/60">A calm ledger of every exchange.</p>
        </div>

        <button
          onClick={() => navigate('/chat')}
          className="flex items-center gap-2 text-[0.65rem] uppercase tracking-[0.4em] text-white/60 hover:text-white transition-colors duration-300 w-fit"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to chat
        </button>

        <LiquidPanel className="space-y-4 px-6 sm:px-8 py-7 sm:py-9">
          <div className="flex items-center gap-3 text-base text-white/60">
            <Clock className="h-5 w-5" />
            <span>Every session is preserved, no extra noise.</span>
          </div>
          {history.length === 0 && !loading ? (
            <p className="text-sm uppercase tracking-[0.4em] text-white/40">Nothing archived yet.</p>
          ) : (
            <div className="flex flex-wrap gap-3 text-[0.65rem] uppercase tracking-[0.3em] text-white/40">
              <span className="liquid-tag">Curated</span>
              <span className="liquid-tag">Minimal</span>
            </div>
          )}
        </LiquidPanel>

        <div className="space-y-4 sm:space-y-5">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="h-12 w-12 animate-spin rounded-full border-4 border-white/20 border-t-white" />
            </div>
          ) : history.length === 0 ? (
            <div className="rounded-3xl border border-white/10 bg-white/5 p-8 sm:p-10 text-center text-base text-white/60">
              No history yet. Ask a question to begin the archive.
            </div>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                className="rounded-3xl border border-white/10 bg-white/5 p-6 sm:p-8 text-sm text-white/70 hover:border-white/20 transition-colors"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-white/5 text-xs uppercase tracking-[0.4em] text-white/50">
                  <span>{item.niche}</span>
                  <span className="flex items-center gap-2 text-white/60">
                    <Clock className="h-4 w-4" />
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="mt-5 space-y-5">
                  <div>
                    <p className="text-[0.65rem] uppercase tracking-[0.4em] text-white/40 mb-2">Question</p>
                    <p className="text-base sm:text-lg text-white break-words">{item.question}</p>
                  </div>
                  <div>
                    <p className="text-[0.65rem] uppercase tracking-[0.4em] text-white/40 mb-2">Answer</p>
                    <p className="text-base sm:text-lg text-white/80 break-words">{item.answer}</p>
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
