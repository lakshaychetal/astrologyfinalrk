import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { CosmicBackground } from '@/components/CosmicBackground';
import { User, Mail, Sparkles, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Profile = () => {
  const { user } = useAuth();
  const { theme } = useTheme();
  const navigate = useNavigate();

  const isDark = theme === 'dark';

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <CosmicBackground />
      <div className="w-full max-w-2xl">
        <button
          onClick={() => navigate('/chat')}
          className={`mb-6 flex items-center gap-2 transition ${isDark ? 'text-slate-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Chat
        </button>

        <div className={`backdrop-blur-xl rounded-2xl p-8 border shadow-2xl ${isDark ? 'bg-slate-900/80 border-slate-700' : 'bg-white/90 border-gray-200'}`}>
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 mb-4 shadow-lg">
              <User className="w-12 h-12 text-white" />
            </div>
            <h1 className={`text-3xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Your Profile</h1>
            <p className={isDark ? 'text-slate-400' : 'text-gray-600'}>Cosmic traveler information</p>
          </div>

          <div className="space-y-6">
            <div className={`rounded-xl p-6 border ${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-gray-50 border-gray-200'}`}>
              <div className="flex items-center gap-3 mb-2">
                <User className={`w-5 h-5 ${isDark ? 'text-violet-400' : 'text-violet-600'}`} />
                <label className={`text-sm font-medium ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>Name</label>
              </div>
              <p className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{user?.name}</p>
            </div>

            <div className={`rounded-xl p-6 border ${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-gray-50 border-gray-200'}`}>
              <div className="flex items-center gap-3 mb-2">
                <Mail className={`w-5 h-5 ${isDark ? 'text-violet-400' : 'text-violet-600'}`} />
                <label className={`text-sm font-medium ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>Email</label>
              </div>
              <p className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{user?.email}</p>
            </div>

            <div className={`rounded-xl p-6 border ${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-gray-50 border-gray-200'}`}>
              <div className="flex items-center gap-3 mb-2">
                <Sparkles className={`w-5 h-5 ${isDark ? 'text-violet-400' : 'text-violet-600'}`} />
                <label className={`text-sm font-medium ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>User ID</label>
              </div>
              <p className={`text-sm font-mono ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>{user?.id}</p>
            </div>
          </div>

          <div className={`mt-8 p-4 rounded-xl border ${isDark ? 'bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 border-violet-500/30' : 'bg-gradient-to-r from-violet-100 to-fuchsia-100 border-violet-300'}`}>
            <p className={`text-center text-sm ${isDark ? 'text-violet-200' : 'text-violet-700'}`}>
              ✨ Your journey through the cosmos continues ✨
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
