import { useState, useEffect, ReactNode, useCallback } from 'react';
import { auth } from '@/lib/api';
import { AuthContext, type User } from '@/contexts/auth-context-base';

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token && token !== 'undefined' && token !== 'null') {
      auth.getProfile()
        .then(res => setUser(res.data.user))
        .catch(() => localStorage.removeItem('token'))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await auth.login({ email, password });
    localStorage.setItem('token', res.data.token);
    setUser(res.data.user);
  }, []);

  const signup = useCallback(async (email: string, password: string, name: string) => {
    const res = await auth.signup({ email, password, name });
    localStorage.setItem('token', res.data.token);
    setUser(res.data.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
