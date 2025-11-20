import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { CosmicBackground } from '@/components/CosmicBackground';
import { Sparkles, Moon, Sun } from 'lucide-react';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const isDark = theme === 'dark';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/chat');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <CosmicBackground />
      <div className="w-full max-w-md">
        <div className="absolute top-4 right-4">
          <button
            onClick={toggleTheme}
            className={`p-3 rounded-full backdrop-blur-xl ${isDark ? 'bg-white/10 hover:bg-white/20' : 'bg-gray-900/10 hover:bg-gray-900/20'} border ${isDark ? 'border-white/20' : 'border-gray-300'} transition`}
          >
            {isDark ? <Sun className="w-5 h-5 text-yellow-300" /> : <Moon className="w-5 h-5 text-slate-700" />}
          </button>
        </div>
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className={`text-4xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Welcome Back</h1>
          <p className={isDark ? 'text-purple-300' : 'text-violet-600'}>Sign in to explore the cosmos</p>
        </div>

        <div className={`backdrop-blur-xl rounded-2xl p-8 border shadow-2xl ${isDark ? 'bg-slate-900/80 border-slate-700' : 'bg-white/90 border-gray-200'}`}>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={`w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-violet-500 transition ${isDark ? 'bg-slate-900/50 border-slate-700 text-white placeholder-slate-500' : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400'}`}
                placeholder="your@email.com"
                required
              />
            </div>

            <div>
              <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-violet-500 transition ${isDark ? 'bg-slate-900/50 border-slate-700 text-white placeholder-slate-500' : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400'}`}
                placeholder="••••••••"
                required
              />
            </div>

            {error && (
              <div className={`p-3 rounded-lg border text-sm ${isDark ? 'bg-red-500/20 border-red-500/50 text-red-200' : 'bg-red-50 border-red-200 text-red-700'}`}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold hover:from-violet-700 hover:to-fuchsia-700 focus:outline-none focus:ring-2 focus:ring-violet-500 transition disabled:opacity-50 shadow-lg"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className={`mt-6 text-center text-sm ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
            Don't have an account?{' '}
            <Link to="/signup" className={`font-semibold ${isDark ? 'text-fuchsia-400 hover:text-fuchsia-300' : 'text-violet-600 hover:text-violet-700'}`}>
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
