import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/useAuth';
import { chat } from '@/lib/api';
import { CosmicBackground } from '@/components/CosmicBackground';
import heartIcon from '@/assets/heart_icon.png';
import careerIcon from '@/assets/career_icon.png';
import wealthIcon from '@/assets/wealth_icon.png';
import healthIcon from '@/assets/health_icon.png';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState('');
  const [niche, setNiche] = useState('Love');
  const [loading, setLoading] = useState(false);
  const [selectedNiche, setSelectedNiche] = useState<string | null>(null);
  const birthDetails = (() => {
    const stored = localStorage.getItem('birthDetails');
    return stored ? JSON.parse(stored) : null;
  })();
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
      icon: heartIcon,
      gradient:
        'radial-gradient(circle at 25% 20%, rgba(255,255,255,0.65), transparent 55%), radial-gradient(circle at 70% 70%, rgba(255,94,180,0.45), transparent 40%), linear-gradient(145deg, rgba(3,3,3,0.95), rgba(6,6,6,0.82))',
    },
    {
      label: 'Career',
      subtitle: 'Purpose & ambition',
      icon: careerIcon,
      gradient:
        'radial-gradient(circle at 20% 40%, rgba(255,255,255,0.5), transparent 55%), radial-gradient(circle at 75% 40%, rgba(78,217,255,0.35), transparent 40%), linear-gradient(140deg, rgba(4,4,4,0.9), rgba(1,18,35,0.85))',
    },
    {
      label: 'Wealth',
      subtitle: 'Abundance flows',
      icon: wealthIcon,
      gradient:
        'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.55), transparent 55%), radial-gradient(circle at 65% 65%, rgba(251,195,66,0.35), transparent 40%), linear-gradient(160deg, rgba(8,8,8,0.95), rgba(15,75,40,0.75))',
    },
    {
      label: 'Health',
      subtitle: 'Body & vitality',
      icon: healthIcon,
      gradient:
        'radial-gradient(circle at 25% 40%, rgba(255,255,255,0.45), transparent 55%), radial-gradient(circle at 70% 70%, rgba(109,255,192,0.35), transparent 40%), linear-gradient(150deg, rgba(3,3,3,0.95), rgba(4,51,47,0.8))',
    },
    {
      label: 'Spirituality',
      subtitle: 'Inner knowing',
      icon: heartIcon,
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
      const res = await chat.ask({ question: prompt, niche });
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

  if (!birthDetails) {
    return null;
  }

  const birthRelationshipLine = `${birthDetails.relationshipStatus} • ${birthDetails.employmentStatus}`;
  const birthMomentLine = `Born ${birthDetails.dob} at ${birthDetails.birthTime} in ${birthDetails.birthPlace}`;

  if (!selectedNiche) {
    return (
      <div className="min-h-screen h-screen relative overflow-hidden bg-black text-white">
        <CosmicBackground />
        <div className="relative z-10 flex h-screen w-full flex-col gap-3 px-3 sm:px-6 py-4 sm:py-6 max-w-6xl mx-auto overflow-hidden">
          <div className="flex items-center justify-between gap-4 pb-2 border-b border-white/5 flex-shrink-0">
            <span className="text-[0.55rem] uppercase tracking-[0.4em] sm:tracking-[0.5em] text-white/40">Choose your niche</span>
          </div>

          <div className="space-y-1.5 sm:space-y-2 flex-shrink-0">
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-semibold tracking-tight">Select a path</h1>
            <p className="text-[0.65rem] sm:text-xs text-white/60 line-clamp-1">{birthMomentLine} • {birthRelationshipLine}</p>
          </div>

          <div className="flex flex-1 flex-col gap-2.5 sm:gap-3 pb-4 overflow-y-auto min-h-0">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-3">
              {nicheCards.slice(0, 4).map((card) => (
                <button
                  key={card.label}
                  type="button"
                  onClick={() => handleCardSelect(card.label)}
                  className="relative flex flex-col items-center justify-center overflow-hidden rounded-xl sm:rounded-2xl bg-gradient-to-br from-black via-black/80 to-black text-white transition-all duration-300 hover:scale-[1.02] hover:shadow-xl focus-visible:outline-none p-4 sm:p-6 min-h-[100px] sm:min-h-[140px]"
                >
                  <div className="absolute inset-0" style={{ backgroundImage: card.gradient }} />
                  <div className="absolute inset-0 bg-black/80 backdrop-blur-[60px]" />
                  <div className="relative flex flex-col items-center gap-2 sm:gap-3 text-center">
                    <img src={card.icon} alt={card.label} className="w-8 h-8 sm:w-10 sm:h-10 object-contain" />
                    <div>
                      <p className="text-xs sm:text-sm font-semibold text-white">{card.label}</p>
                      <p className="text-[0.6rem] text-white/50 mt-0.5 sm:mt-1">{card.subtitle}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-1 gap-2.5 sm:gap-3">
              {nicheCards.slice(4).map((card) => (
                <button
                  key={card.label}
                  type="button"
                  onClick={() => handleCardSelect(card.label)}
                  className="relative flex flex-col items-center justify-center overflow-hidden rounded-xl sm:rounded-2xl bg-gradient-to-br from-black via-black/80 to-black text-white transition-all duration-300 hover:scale-[1.02] hover:shadow-xl focus-visible:outline-none p-4 sm:p-6 min-h-[90px] sm:min-h-[120px]"
                >
                  <div className="absolute inset-0" style={{ backgroundImage: card.gradient }} />
                  <div className="absolute inset-0 bg-black/80 backdrop-blur-[60px]" />
                  <div className="relative flex flex-col items-center gap-2 sm:gap-3 text-center">
                    <img src={card.icon} alt={card.label} className="w-8 h-8 sm:w-10 sm:h-10 object-contain" />
                    <div>
                      <p className="text-xs sm:text-sm font-semibold text-white">{card.label}</p>
                      <p className="text-[0.6rem] text-white/50 mt-0.5 sm:mt-1">{card.subtitle}</p>
                    </div>
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
      <div className="relative z-10 flex h-screen w-full flex-col gap-3 px-3 sm:px-6 py-4 sm:py-6 max-w-6xl mx-auto overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-white/10 pb-2 gap-2 text-[0.55rem] uppercase tracking-[0.6em] text-white/40 flex-shrink-0">
          <span>Selected niche</span>
          <strong className="text-base sm:text-xl tracking-tight text-white">{selectedNiche}</strong>
        </div>


        <div className="relative flex flex-1 flex-col items-center justify-center gap-3 sm:gap-4 py-2 sm:py-4 min-h-0">
          <div
            className={`relative flex flex-col items-center gap-2 sm:gap-3 transition-all duration-700 ${
              bubbleStage === 'top' ? '-translate-y-4 sm:-translate-y-6' : bubbleStage === 'thinking' ? 'translate-y-1 sm:translate-y-2' : 'translate-y-0'
            }`}
          >
            <div className="relative flex items-center justify-center">
              <div className="bubble-glow scale-75 sm:scale-100" />
              <div className={`bubble-core scale-75 sm:scale-100 ${bubbleStage !== 'center' ? 'bubble-top' : ''}`} />
            </div>
            <p className="text-[0.6rem] sm:text-xs uppercase tracking-[0.3em] sm:tracking-[0.4em] text-white/60 text-center px-4">
              {bubbleStage === 'thinking'
                ? 'Divine source is composing'
                : bubbleStage === 'top'
                ? 'Listening closely'
                : bubbleStage === 'answered'
                ? 'Answer received'
                : 'Awaiting your question'}
            </p>
            {bubbleStage !== 'center' && (floatingQuestion || question) && (
              <div className="rounded-full border border-white/10 bg-white/5 px-3 sm:px-6 py-1.5 sm:py-2 text-[0.6rem] sm:text-xs uppercase tracking-[0.25em] sm:tracking-[0.3em] text-white/70 shadow-[0_15px_40px_rgba(0,0,0,0.6)] max-w-[90%] text-center">
                {floatingQuestion || question}
              </div>
            )}
          </div>

          {showChips && (
            <div className="grid w-full grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 max-w-3xl overflow-y-auto max-h-[30vh] sm:max-h-none">
              {questionChips.map((prompt) => (
                <button key={prompt} type="button" onClick={() => handlePresetQuestion(prompt)} className="chip-tone">
                  <span className="text-[0.6rem] font-semibold uppercase tracking-[0.3em] text-white/70">Ask</span>
                  <p className="text-xs sm:text-sm leading-tight text-white">{prompt}</p>
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
              className="text-[0.6rem] sm:text-xs uppercase tracking-[0.3em] sm:tracking-[0.4em] text-white/50 underline-offset-4 hover:text-white transition-colors duration-300"
            >
              Ask another question
            </button>
          )}
        </div>

        <div className="flex flex-col gap-3 sm:gap-4 w-full flex-shrink-0">
          <div className="flex flex-col rounded-xl sm:rounded-2xl border border-white/10 bg-black/90 px-3 sm:px-4 py-3 sm:py-4 shadow-[0_30px_90px_rgba(0,0,0,0.75)] h-[180px] sm:h-[200px]">
            <div className="mb-2 flex items-center justify-between text-[0.55rem] uppercase tracking-[0.4em] sm:tracking-[0.5em] text-white/40 pb-2 border-b border-white/5 flex-shrink-0">
              <span>Live prompt</span>
              <span className="truncate max-w-[100px] sm:max-w-[150px]">{user?.name ?? 'Traveler'}</span>
            </div>
            <div className="flex-1 space-y-2 sm:space-y-3 overflow-y-auto pr-1 sm:pr-2 min-h-0">
              {messages.length === 0 ? (
                <div className="text-center text-xs text-white/40 py-4">The halo waits for your question.</div>
              ) : (
                messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`rounded-xl sm:rounded-2xl border px-2.5 sm:px-3 py-2 sm:py-2.5 text-xs sm:text-sm shadow-[0_20px_45px_rgba(0,0,0,0.6)] ${
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
                <div className="flex gap-1.5 sm:gap-2 py-2 sm:py-3">
                  <span className="h-2 w-2 sm:h-2.5 sm:w-2.5 rounded-full bg-white/70 animate-pulse" />
                  <span className="h-2 w-2 sm:h-2.5 sm:w-2.5 rounded-full bg-white/40 animate-pulse" />
                  <span className="h-2 w-2 sm:h-2.5 sm:w-2.5 rounded-full bg-white/20 animate-pulse" />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="flex gap-2">
              <div className="flex-1 gradient-sender">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Message GPT-5"
                  className="w-full rounded-[36px] border border-transparent bg-transparent px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm text-white placeholder:text-white/70 focus:border-transparent focus:outline-none"
                  disabled={loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="gradient-send-btn rounded-[36px] px-4 sm:px-5 py-2 sm:py-2.5 text-xs sm:text-sm font-semibold text-white transition-all duration-300 hover:opacity-90 hover:scale-105 disabled:opacity-50 disabled:scale-100"
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
