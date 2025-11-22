import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && token !== 'undefined' && token !== 'null') {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const auth = {
  signup: (data: { email: string; password: string; name: string }) =>
    api.post('/api/signup', data),
  login: (data: { email: string; password: string }) =>
    api.post('/api/login', data),
  getProfile: () => api.get('/api/me'),
};

export const birthDetails = {
  submit: (data: {
    name: string;
    gender: string;
    dob: string;
    birthTime: string;
    birthPlace: string;
    latitude: number;
    longitude: number;
    relationshipStatus: string;
    employmentStatus: string;
  }) => api.post('/api/birth-details', data),
  get: () => api.get('/api/birth-details'),
};

export const chat = {
  ask: (data: { question: string; niche: string }) =>
    api.post('/api/chat', data),
  getHistory: () => api.get('/api/chat/history'),
};

export default api;
