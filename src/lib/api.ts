import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const auth = {
  signup: (data: { email: string; password: string; name: string }) =>
    api.post('/signup', data),
  login: (data: { email: string; password: string }) =>
    api.post('/login', data),
  getProfile: () => api.get('/me'),
};

export const chat = {
  ask: (data: { question: string; chart_data: string; niche: string }) =>
    api.post('/chat', data),
  getHistory: () => api.get('/chat/history'),
};

export default api;
