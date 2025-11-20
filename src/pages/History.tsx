import { useState, useEffect } from 'react';
import { chat } from '@/lib/api';
import { useTheme } from '@/contexts/ThemeContext';
import { CosmicBackground } from '@/components/CosmicBackground';
import { ArrowLeft, MessageCircle, Clock } from 'lucide-react';
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
  const { theme } = useTheme();
  const navigate = useNavigate();

  const isDark = theme === 'dark';

  useEffect(() => {
    chat.getHistory()
      .then(res => setHistory(res.data.history || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen p-4">
      <CosmicBackground />
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate('/chat')}
          className={`mb-6 flex items-center gap-2 transition ${isDark ? 'text-slate-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Chat
        </button>

        <div className={`backdrop-blur-xl rounded-2xl p-8 border shadow-2xl ${isDark ? 'bg-slate-900/80 border-slate-700' : 'bg-white/90 border-gray-200'}`}>
          <div className="flex items-center gap-3 mb-8">
            <MessageCircle className={`w-8 h-8 ${isDark ? 'text-violet-400' : 'text-violet-600'}`} />
            <div>
              <h1 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Chat History</h1>
              <p className={isDark ? 'text-slate-400' : 'text-gray-600'}>Your cosmic conversations</p>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block w-8 h-8 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-12">
              <MessageCircle className={`w-16 h-16 mx-auto mb-4 ${isDark ? 'text-violet-400/50' : 'text-violet-300'}`} />
              <p className={isDark ? 'text-slate-400' : 'text-gray-600'}>No conversations yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((item) => (
                <div key={item.id} className={`rounded-xl p-6 border transition ${isDark ? 'bg-slate-800/50 border-slate-700 hover:bg-slate-800' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'}`}>
                  <div className="flex items-start justify-between mb-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${isDark ? 'bg-violet-500/20 text-violet-300' : 'bg-violet-100 text-violet-700'}`}>
                      {item.niche}
                    </span>
                    <div className={`flex items-center gap-2 text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                      <Clock className="w-3 h-3" />
                      {new Date(item.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className={`text-sm mb-1 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>Question:</p>
                      <p className={isDark ? 'text-white' : 'text-gray-900'}>{item.question}</p>
                    </div>
                    <div>
                      <p className={`text-sm mb-1 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>Answer:</p>
                      <p className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>{item.answer}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
