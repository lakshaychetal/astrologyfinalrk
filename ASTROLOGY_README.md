# 🌟 Astrology AI - Cosmic Frontend

Professional React app for Astrology AI with dark/light mode and all user endpoints implemented.

## ✨ Features Implemented

### Theme System
- 🌙 **Dark Mode** - Professional dark theme with slate colors
- ☀️ **Light Mode** - Clean light theme with violet accents
- 💾 **Persistent** - Theme preference saved to localStorage
- 🎨 **Color Constants** - Centralized color management

### Authentication
- ✅ **Signup** - Create new account with email, password, and name
- ✅ **Login** - Sign in with email and password
- ✅ **Profile** - View user profile information
- ✅ **Protected Routes** - Automatic redirect based on auth state

### AI Chat
- ✅ **Ask Questions** - Send questions with chart data and niche
- ✅ **Chat History** - View all previous conversations
- ✅ **Real-time Chat UI** - Beautiful message interface

### Design
- 🎨 Professional gradient backgrounds
- ⭐ Animated twinkling stars (dark mode)
- 💫 Glassmorphism effects
- 🌈 Violet/fuchsia gradient accents
- 📱 Fully responsive
- 🎯 Consistent color palette across modes

## 🚀 Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the dev server:**
   ```bash
   npm run dev
   ```

3. **Make sure your backend is running on:**
   ```
   http://localhost:5000
   ```

## 📁 Project Structure

```
src/
├── components/
│   └── CosmicBackground.tsx    # Theme-aware animated background
├── contexts/
│   ├── AuthContext.tsx         # Authentication state management
│   └── ThemeContext.tsx        # Theme state management
├── lib/
│   ├── api.ts                  # API service with axios
│   └── colors.ts               # Color constants for themes
├── pages/
│   ├── Login.tsx               # Login page with theme toggle
│   ├── Signup.tsx              # Signup page with theme toggle
│   ├── Chat.tsx                # AI chat interface
│   ├── Profile.tsx             # User profile
│   └── History.tsx             # Chat history
└── App.tsx                     # Routes and providers
```

## 🎯 API Endpoints Used

- `POST /api/signup` - Create account
- `POST /api/login` - Sign in
- `GET /api/me` - Get profile
- `POST /api/chat` - Ask question
- `GET /api/chat/history` - Get chat history

## 🎨 Color Palette

### Dark Mode
- Background: Slate-950, Purple-950, Slate-900
- Cards: Slate-800/900 with transparency
- Text: White, Slate-300, Slate-400
- Accents: Violet-400, Fuchsia-400
- Borders: Slate-700

### Light Mode
- Background: Violet-50, Purple-50, Fuchsia-50
- Cards: White/Gray-50 with transparency
- Text: Gray-900, Gray-700, Gray-600
- Accents: Violet-600, Fuchsia-600
- Borders: Gray-200/300

### Shared
- Gradients: Violet-600 to Fuchsia-600
- Shadows: Professional elevation

## 🔐 Authentication Flow

1. User signs up or logs in
2. JWT token stored in localStorage
3. Token automatically added to API requests
4. Protected routes check auth state
5. Logout clears token and redirects

Enjoy exploring the cosmos! ✨🌌
