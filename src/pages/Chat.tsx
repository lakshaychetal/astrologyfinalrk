import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/useAuth';
import { chat } from '@/lib/api';
import { CosmicBackground } from '@/components/CosmicBackground';
import { PlanetOrbit } from '@/components/PlanetOrbit';
import { BirthDetailWizard, type BirthDetails } from '@/components/BirthDetailWizard';
import { ArrowUpRight } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState('');
  const [chartData, setChartData] = useState('');
  const [niche, setNiche] = useState('Love');
  const [loading, setLoading] = useState(false);
  const [selectedNiche, setSelectedNiche] = useState<string | null>(null);
  const [birthDetails, setBirthDetails] = useState<BirthDetails | null>(null);
  const [bubbleStage, setBubbleStage] = useState<'center' | 'top' | 'thinking' | 'answered'>('center');
  const [showChips, setShowChips] = useState(false);
  const [floatingQuestion, setFloatingQuestion] = useState('');
  const bubbleResetRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { user } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const nicheCards = [
    {
      label: 'Love',
      subtitle: 'Relationships & heart',
      gradient:
        'radial-gradient(circle at 25% 20%, rgba(255,255,255,0.65), transparent 55%), radial-gradient(circle at 70% 70%, rgba(255,94,180,0.45), transparent 40%), linear-gradient(145deg, rgba(3,3,3,0.95), rgba(6,6,6,0.82))',
    },
    {
      label: 'Career',
      subtitle: 'Purpose & ambition',
      gradient:
        'radial-gradient(circle at 20% 40%, rgba(255,255,255,0.5), transparent 55%), radial-gradient(circle at 75% 40%, rgba(78,217,255,0.35), transparent 40%), linear-gradient(140deg, rgba(4,4,4,0.9), rgba(1,18,35,0.85))',
    },
    {
      label: 'Wealth',
      subtitle: 'Abundance flows',
      gradient:
        'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.55), transparent 55%), radial-gradient(circle at 65% 65%, rgba(251,195,66,0.35), transparent 40%), linear-gradient(160deg, rgba(8,8,8,0.95), rgba(15,75,40,0.75))',
    },
    {
      label: 'Health',
      subtitle: 'Body & vitality',
      gradient:
        'radial-gradient(circle at 25% 40%, rgba(255,255,255,0.45), transparent 55%), radial-gradient(circle at 70% 70%, rgba(109,255,192,0.35), transparent 40%), linear-gradient(150deg, rgba(3,3,3,0.95), rgba(4,51,47,0.8))',
    },
    {
      label: 'Spirituality',
      subtitle: 'Inner knowing',
      gradient:
        'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.55), transparent 55%), radial-gradient(circle at 65% 50%, rgba(172,150,255,0.35), transparent 40%), linear-gradient(135deg, rgba(5,5,5,0.95), rgba(25,8,54,0.82))',
    },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const questionChips = [
    'What should I focus on now?',
    'Where is my energy strongest?',
    'How can I deepen my relationships?',
    'What path leads to abundance this season?',
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const prompt = question.trim();
    if (!prompt) return;

    if (bubbleResetRef.current) {
      clearTimeout(bubbleResetRef.current);
    }

    setMessages([]);
    setFloatingQuestion(prompt);
    setQuestion('');
    setLoading(true);
    setBubbleStage('thinking');

    try {
      const res = await chat.ask({ question: prompt, chart_data: chartData, niche });
      setMessages([{ role: 'assistant', content: res.data.answer }]);
      setBubbleStage('answered');
      bubbleResetRef.current = setTimeout(() => setBubbleStage('center'), 2200);
  } catch (_err: unknown) {
      setMessages([
        {
          role: 'assistant',
          content: 'Sorry, I ran into an error. Try again in a moment.',
        },
      ]);
      setBubbleStage('answered');
      bubbleResetRef.current = setTimeout(() => setBubbleStage('center'), 2200);
    } finally {
      setLoading(false);
      setFloatingQuestion('');
    }
  };

  const handleCardSelect = (option: string) => {
    setSelectedNiche(option);
    setNiche(option);
    setMessages([]);
    setQuestion('');
    setChartData('');
    setShowChips(true);
    setBubbleStage('center');
    setFloatingQuestion('');
  };

  const handlePresetQuestion = (prompt: string) => {
    setQuestion(prompt);
    setFloatingQuestion(prompt);
    setShowChips(false);
    setBubbleStage('top');
  };

  const handleWizardComplete = (details: BirthDetails) => {
    setBirthDetails(details);
    setChartData(JSON.stringify(details));
  };

  if (!birthDetails) {
    return <BirthDetailWizard onComplete={handleWizardComplete} />;
  }

  const birthSummaryLine = `${birthDetails.name} • ${birthDetails.gender}`;
  const birthRelationshipLine = `${birthDetails.relationshipStatus} • ${birthDetails.employmentStatus}`;
  const birthMomentLine = `Born ${birthDetails.dob} at ${birthDetails.birthTime} in ${birthDetails.birthPlace}`;

  if (!selectedNiche) {
    return (
      <div className="min-h-screen relative overflow-hidden bg-black text-white">
        <CosmicBackground />
        <div className="relative z-10 flex h-screen w-full flex-col gap-6 px-6 py-8">
          <div className="flex items-center justify-between gap-4">
            <span className="text-[0.6rem] uppercase tracking-[0.5em] text-white/40">Choose your niche</span>
            <PlanetOrbit size="sm" className="pointer-events-none text-white/50 scale-75" />
          </div>

          <div>
            <h1 className="text-3xl font-semibold tracking-tight">{selectedNiche ? selectedNiche : 'Select a path'}</h1>
            <p className="text-sm text-white/60">{birthMomentLine} • {birthRelationshipLine}</p>
          </div>

          <div className="flex flex-1 flex-col gap-4">
            <div className="grid flex-1 grid-cols-2 gap-3">
              {nicheCards.slice(0, 4).map((card) => (
                <button
                  key={card.label}
                  type="button"
                  onClick={() => handleCardSelect(card.label)}
                  className="relative flex h-full w-full overflow-hidden rounded-[22px] bg-gradient-to-br from-black via-black/80 to-black text-left text-white transition focus-visible:outline-none"
                >
                  <div className="absolute inset-0" style={{ backgroundImage: card.gradient }} />
                  <div className="absolute inset-0 bg-black/80 backdrop-blur-[60px]" />
                  <div className="relative flex h-full flex-col justify-end gap-2 px-4 py-4">
                    <div className="flex items-center justify-between text-[0.55rem] uppercase tracking-[0.5em] text-white/60">
                      <span>{card.label}</span>
                      <ArrowUpRight className="h-4 w-4" />
                    </div>
                    <p className="text-[0.65rem] text-white/50">{card.subtitle}</p>
                  </div>
                </button>
              ))}
            </div>

            <div className="grid flex-1 grid-cols-2 gap-3">
              {nicheCards.slice(4).map((card) => (
                <button
                  key={card.label}
                  type="button"
                  onClick={() => handleCardSelect(card.label)}
                  className="relative flex h-full w-full overflow-hidden rounded-[22px] bg-gradient-to-br from-black via-black/80 to-black text-left text-white transition focus-visible:outline-none"
                >
                  <div className="absolute inset-0" style={{ backgroundImage: card.gradient }} />
                  <div className="absolute inset-0 bg-black/80 backdrop-blur-[60px]" />
                  <div className="relative flex h-full flex-col justify-end gap-2 px-4 py-4">
                    <div className="flex items-center justify-between text-[0.55rem] uppercase tracking-[0.5em] text-white/60">
                      <span>{card.label}</span>
                      <ArrowUpRight className="h-4 w-4" />
                    </div>
                    <p className="text-[0.65rem] text-white/50">{card.subtitle}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative overflow-hidden bg-black text-white">
      <CosmicBackground />
      <div className="absolute inset-0 bg-black/95" aria-hidden />
      <div className="relative z-10 flex min-h-screen w-full flex-col gap-6 px-6 py-8">
        <div className="flex items-center justify-between border-b border-white/10 pb-2 text-[0.55rem] uppercase tracking-[0.6em] text-white/40">
          <div className="flex items-center gap-2">
            <PlanetOrbit size="sm" className="text-white/60 scale-75" />
            <span>Selected niche</span>
          </div>
          <strong className="text-xl tracking-tight text-white">{selectedNiche}</strong>
        </div>

        <div className="space-y-1 text-sm text-white/60">
          <p>A divine, Apple-inspired space for GPT-style insight.</p>
          <p className="text-[0.55rem] uppercase tracking-[0.4em] text-white/60">{birthSummaryLine}</p>
          <p className="text-[0.65rem] text-white/50">{birthMomentLine} • {birthRelationshipLine}</p>
        </div>

        <div className="relative flex flex-1 flex-col items-center justify-center gap-5">
          <div
            className={`relative flex flex-col items-center gap-2 transition-all duration-700 ${
              bubbleStage === 'top' ? '-translate-y-6' : bubbleStage === 'thinking' ? 'translate-y-2' : 'translate-y-0'
            }`}
          >
            <div className="relative flex items-center justify-center">
              <div className="bubble-glow" />
              <div className={`bubble-core ${bubbleStage !== 'center' ? 'bubble-top' : ''}`} />
            </div>
            <p className="text-xs uppercase tracking-[0.4em] text-white/60">
              {bubbleStage === 'thinking'
                ? 'Divine source is composing'
                : bubbleStage === 'top'
                ? 'Listening closely'
                : bubbleStage === 'answered'
                ? 'Answer received'
                : 'Awaiting your question'}
            </p>
            {bubbleStage !== 'center' && (floatingQuestion || question) && (
              <div className="rounded-full border border-white/10 bg-white/5 px-5 py-2 text-xs uppercase tracking-[0.3em] text-white/70 shadow-[0_15px_40px_rgba(0,0,0,0.6)]">
                {floatingQuestion || question}
              </div>
            )}
          </div>

          {showChips && (
            <div className="grid w-full grid-cols-2 gap-3">
              {questionChips.map((prompt) => (
                <button key={prompt} type="button" onClick={() => handlePresetQuestion(prompt)} className="chip-tone">
                  <span className="text-[0.65rem] font-semibold uppercase tracking-[0.35em] text-white/70">Ask</span>
                  <p className="text-sm leading-tight text-white">{prompt}</p>
                </button>
              ))}
            </div>
          )}
          {!showChips && bubbleStage === 'center' && (
            <button
              type="button"
              onClick={() => {
                setShowChips(true);
                setBubbleStage('center');
                setFloatingQuestion('');
              }}
              className="text-xs uppercase tracking-[0.4em] text-white/50 underline-offset-4 hover:text-white"
            >
              Ask another question
            </button>
          )}
        </div>

        <div className="flex flex-1 flex-col gap-3">
          <div className="flex flex-1 flex-col rounded-[32px] border border-white/10 bg-black/90 px-5 py-5 shadow-[0_30px_90px_rgba(0,0,0,0.75)]">
            <div className="mb-3 flex items-center justify-between text-[0.6rem] uppercase tracking-[0.5em] text-white/40">
              <span>Live prompt</span>
              <span>{user?.name ?? 'Traveler'}</span>
            </div>
            <div className="flex-1 space-y-4 overflow-y-auto pr-1">
              {messages.length === 0 ? (
                <div className="text-center text-white/40">The halo waits for your question.</div>
              ) : (
                messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`rounded-[28px] border px-4 py-3 text-sm shadow-[0_20px_45px_rgba(0,0,0,0.6)] ${
                      msg.role === 'user'
                        ? 'border-white/20 bg-gradient-to-br from-[#050b18] via-[#030612] to-[#01030c] text-white'
                        : 'border-white/20 bg-white/5 text-white/70'
                    }`}
                  >
                    {msg.content}
                  </div>
                ))
              )}
              {loading && (
                <div className="flex gap-2">
                  <span className="h-2 w-2 rounded-full bg-white/70 animate-pulse" />
                  <span className="h-2 w-2 rounded-full bg-white/40 animate-pulse" />
                  <span className="h-2 w-2 rounded-full bg-white/20 animate-pulse" />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3 pt-1">
            <div className="flex gap-3">
              <div className="flex-1 gradient-sender">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Message GPT-5"
                  className="w-full rounded-[32px] border border-transparent bg-transparent px-5 py-3 text-sm text-white placeholder:text-white/70 focus:border-transparent focus:outline-none"
                  disabled={loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="gradient-send-btn rounded-[32px] px-5 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
