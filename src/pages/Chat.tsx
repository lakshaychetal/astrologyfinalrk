import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { chat } from '@/lib/api';
import { CosmicBackground } from '@/components/CosmicBackground';
import { Send, Sparkles, User, LogOut, History, Moon, Sun } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState('');
  const [chartData, setChartData] = useState('');
  const [niche, setNiche] = useState('Love & Relationships');
  const [loading, setLoading] = useState(false);
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const isDark = theme === 'dark';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userMessage = { role: 'user' as const, content: question };
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setLoading(true);

    try {
      const res = await chat.ask({ question, chart_data: chartData, niche });
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.answer }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <CosmicBackground />
      
      <header className={`backdrop-blur-xl border-b sticky top-0 z-10 ${isDark ? 'bg-slate-900/80 border-slate-700' : 'bg-white/80 border-gray-200'}`}>
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center shadow-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Astrology AI</h1>
              <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>Your cosmic guide</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg transition ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <button
              onClick={() => navigate('/history')}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
            >
              <History className="w-4 h-4" />
              <span className="hidden sm:inline">History</span>
            </button>
            <button
              onClick={() => navigate('/profile')}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
            >
              <User className="w-4 h-4" />
              <span className="hidden sm:inline">{user?.name}</span>
            </button>
            <button
              onClick={logout}
              className={`p-2 rounded-lg transition ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col">
        <div className="flex-1 overflow-y-auto mb-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <Sparkles className="w-10 h-10 text-white" />
                </div>
                <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Ask the Stars</h2>
                <p className={isDark ? 'text-slate-400' : 'text-gray-600'}>Enter your chart data and question below</p>
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] p-4 rounded-2xl shadow-lg ${
                  msg.role === 'user' 
                    ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white' 
                    : isDark
                    ? 'bg-slate-800/90 border border-slate-700 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex justify-start">
              <div className={`p-4 rounded-2xl shadow-lg ${isDark ? 'bg-slate-800/90 border border-slate-700' : 'bg-white border border-gray-200'}`}>
                <div className="flex gap-2">
                  <div className="w-2 h-2 rounded-full bg-violet-500 animate-bounce" />
                  <div className="w-2 h-2 rounded-full bg-violet-500 animate-bounce delay-100" />
                  <div className="w-2 h-2 rounded-full bg-violet-500 animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className={`backdrop-blur-xl rounded-2xl p-4 border shadow-lg ${isDark ? 'bg-slate-900/80 border-slate-700' : 'bg-white/90 border-gray-200'}`}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            <input
              type="text"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              placeholder="Niche (e.g., Love & Relationships)"
              className={`px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-violet-500 text-sm ${isDark ? 'bg-slate-900/50 border-slate-700 text-white placeholder-slate-500' : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400'}`}
            />
            <textarea
              value={chartData}
              onChange={(e) => setChartData(e.target.value)}
              placeholder="Chart data (optional)"
              className={`px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-violet-500 text-sm resize-none ${isDark ? 'bg-slate-900/50 border-slate-700 text-white placeholder-slate-500' : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400'}`}
              rows={1}
            />
          </div>
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask your question..."
              className={`flex-1 px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-violet-500 ${isDark ? 'bg-slate-900/50 border-slate-700 text-white placeholder-slate-500' : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400'}`}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold hover:from-violet-700 hover:to-fuchsia-700 focus:outline-none focus:ring-2 focus:ring-violet-500 transition disabled:opacity-50 shadow-lg"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};
