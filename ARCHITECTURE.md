# 🏗️ System Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                         │
│  (Frontend App / Postman / cURL / Mobile App)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FLASK REST API                          │
│                        (api.py)                              │
│                                                              │
│  Routes:                                                     │
│  • /api/signup, /api/login                                  │
│  • /api/me                                                   │
│  • /api/admin/users (CRUD)                                  │
│  • /api/chat, /api/chat/history                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   AUTHENTICATION LAYER                       │
│                        (auth.py)                             │
│                                                              │
│  • JWT Token Generation                                      │
│  • Token Validation                                          │
│  • Password Hashing (bcrypt)                                │
│  • Role-based Authorization                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
        ┌──────────────────┐  ┌──────────────────┐
        │   DATABASE       │  │   AI COMPONENTS  │
        │  (database.py)   │  │   (agents/)      │
        │                  │  │                  │
        │  MongoDB Atlas   │  │  • Chart Parser  │
        │  • users         │  │  • Orchestrator  │
        │  • chats         │  │  • RAG Retriever │
        └──────────────────┘  │  • Synthesizer   │
                              │  • Embeddings    │
                              └──────────────────┘
```

---

## Request Flow

### 1. User Signup/Login
```
Client
  │
  ├─► POST /api/signup
  │     │
  │     ├─► Validate input
  │     ├─► Hash password (bcrypt)
  │     ├─► Store in MongoDB
  │     └─► Generate JWT token
  │           │
  │           └─► Return token to client
  │
  └─► POST /api/login
        │
        ├─► Validate credentials
        ├─► Verify password
        └─► Generate JWT token
              │
              └─► Return token to client
```

### 2. Authenticated Request
```
Client (with token)
  │
  ├─► Request with Authorization header
  │     │
  │     ├─► Extract token
  │     ├─► Validate token (JWT)
  │     ├─► Check expiry
  │     ├─► Extract user info
  │     │
  │     └─► Process request
  │           │
  │           └─► Return response
```

### 3. Admin Request
```
Admin Client (with admin token)
  │
  ├─► Request to /api/admin/*
  │     │
  │     ├─► Validate token
  │     ├─► Check is_admin flag
  │     │
  │     ├─► If admin:
  │     │     └─► Process request
  │     │
  │     └─► If not admin:
  │           └─► Return 403 Forbidden
```

### 4. AI Chat Request
```
User Client (with token)
  │
  ├─► POST /api/chat
  │     │
  │     ├─► Validate token
  │     ├─► Extract user_id
  │     │
  │     ├─► Parse chart data
  │     │     └─► ChartParser.parse_chart_text()
  │     │
  │     ├─► Call AI Orchestrator
  │     │     │
  │     │     ├─► Generate embeddings
  │     │     ├─► Retrieve from RAG
  │     │     ├─► Synthesize response
  │     │     └─► Return answer
  │     │
  │     ├─► Store in MongoDB (chats collection)
  │     │
  │     └─► Return response to client
```

---

## Database Schema

### users Collection
```javascript
{
  _id: ObjectId("65f1234567890abcdef12345"),
  email: "user@example.com",           // Unique index
  password: "$2b$12$hashed...",         // bcrypt hash
  name: "John Doe",
  is_admin: false,                      // Role flag
  active: true,                         // Account status
  created_at: ISODate("2024-01-15T10:30:00Z")
}
```

### chats Collection
```javascript
{
  _id: ObjectId("65f1234567890abcdef12346"),
  user_id: "65f1234567890abcdef12345", // Index on this field
  question: "How will my spouse look?",
  chart_data: "RASHI CHART (D1):\n...",
  niche: "Love & Relationships",
  response: "Based on your chart...",
  timestamp: ISODate("2024-01-15T14:30:00Z")
}
```

---

## Authentication Flow

```
┌──────────┐
│  Client  │
└────┬─────┘
     │
     │ 1. POST /api/login
     │    {email, password}
     ▼
┌─────────────┐
│  API Server │
└─────┬───────┘
      │
      │ 2. Verify credentials
      │    bcrypt.checkpw()
      ▼
┌──────────┐
│ MongoDB  │
└────┬─────┘
     │
     │ 3. User found & verified
     ▼
┌─────────────┐
│  JWT Token  │
│  Generator  │
└─────┬───────┘
      │
      │ 4. Generate token
      │    jwt.encode({user_id, email, is_admin})
      ▼
┌──────────┐
│  Client  │ ← Token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
└──────────┘
```

---

## Authorization Levels

### Public Endpoints (No Auth)
- POST /api/signup
- POST /api/login
- GET /health

### User Endpoints (Token Required)
- GET /api/me
- POST /api/chat
- GET /api/chat/history

### Admin Endpoints (Admin Token Required)
- GET /api/admin/users
- GET /api/admin/users/:id
- POST /api/admin/users
- PUT /api/admin/users/:id
- DELETE /api/admin/users/:id

---

## AI Components Integration

```
┌─────────────────────────────────────────────┐
│           Smart Orchestrator                 │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │  1. Question Complexity Classifier  │    │
│  └────────────────────────────────────┘    │
│                    │                         │
│                    ▼                         │
│  ┌────────────────────────────────────┐    │
│  │  2. Chart Parser                    │    │
│  │     • Extract factors               │    │
│  │     • Parse D1, D9, D10             │    │
│  └────────────────────────────────────┘    │
│                    │                         │
│                    ▼                         │
│  ┌────────────────────────────────────┐    │
│  │  3. Embeddings Generator            │    │
│  │     • Gemini text-embedding-004     │    │
│  └────────────────────────────────────┘    │
│                    │                         │
│                    ▼                         │
│  ┌────────────────────────────────────┐    │
│  │  4. RAG Retriever                   │    │
│  │     • Vertex AI RAG Engine          │    │
│  │     • Classical texts corpus        │    │
│  └────────────────────────────────────┘    │
│                    │                         │
│                    ▼                         │
│  ┌────────────────────────────────────┐    │
│  │  5. Synthesizer                     │    │
│  │     • OpenRouter GPT-4.1 Mini       │    │
│  │     • Generate final response       │    │
│  └────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

---

## Security Layers

```
┌─────────────────────────────────────────┐
│         Security Layer 1: CORS          │
│  • Allow cross-origin requests          │
│  • Configure allowed origins            │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Security Layer 2: JWT Token        │
│  • Validate token signature             │
│  • Check expiry (24 hours)              │
│  • Extract user claims                  │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│   Security Layer 3: Role Authorization  │
│  • Check is_admin flag                  │
│  • Verify user permissions              │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│   Security Layer 4: Password Hashing    │
│  • bcrypt with salt                     │
│  • Never store plain passwords          │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│    Security Layer 5: Active Status      │
│  • Check user.active flag               │
│  • Block inactive accounts              │
└─────────────────────────────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│              Google Cloud Run                    │
│                                                  │
│  ┌────────────────────────────────────────┐   │
│  │         Flask API Container             │   │
│  │                                          │   │
│  │  • Python 3.10+                         │   │
│  │  • Flask + dependencies                 │   │
│  │  • AI agents                            │   │
│  │  • 2 vCPU, 2 GiB RAM                   │   │
│  └────────────────────────────────────────┘   │
│                                                  │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  MongoDB     │ │ Vertex   │ │  OpenRouter  │
│  Atlas       │ │ AI       │ │  API         │
│              │ │          │ │              │
│  • users     │ │ • RAG    │ │ • GPT-4.1    │
│  • chats     │ │ • Embed  │ │   Mini       │
└──────────────┘ └──────────┘ └──────────────┘
```

---

## File Structure

```
astrologyfinalrk/
│
├── api.py                    # Main Flask API
├── auth.py                   # JWT authentication
├── database.py               # MongoDB connection
├── config.py                 # Configuration
├── create_admin.py           # Admin setup script
├── test_api.py               # API tests
│
├── agents/                   # AI components
│   ├── simple_chart_parser.py
│   ├── smart_orchestrator.py
│   ├── gemini_embeddings.py
│   ├── openrouter_synthesizer.py
│   └── ...
│
├── niche_instructions/       # Niche prompts
│   ├── love.py
│   ├── career.py
│   └── ...
│
├── utils/                    # Utilities
│   ├── cache_manager.py
│   └── conversation_manager.py
│
└── docs/                     # Documentation
    ├── API_README.md
    ├── SETUP_GUIDE.md
    ├── IMPLEMENTATION_SUMMARY.md
    ├── ARCHITECTURE.md
    └── QUICK_REFERENCE.md
```

---

## Technology Stack

### Backend
- **Flask** - REST API framework
- **PyJWT** - JWT token handling
- **bcrypt** - Password hashing
- **pymongo** - MongoDB driver

### Database
- **MongoDB Atlas** - Cloud database
  - users collection
  - chats collection

### AI/ML
- **Vertex AI** - RAG Engine, Embeddings
- **OpenRouter** - GPT-4.1 Mini synthesis
- **Gemini** - Embeddings (text-embedding-004)

### Authentication
- **JWT** - Token-based auth
- **bcrypt** - Password hashing

---

## Performance Considerations

### API Response Times
- **Login/Signup:** < 500ms
- **Get Profile:** < 100ms
- **Admin CRUD:** < 200ms
- **AI Chat:** 6-12 seconds (AI processing)
- **Chat History:** < 200ms

### Scalability
- **Stateless API** - Easy horizontal scaling
- **MongoDB Atlas** - Auto-scaling database
- **Cloud Run** - Auto-scaling containers
- **JWT tokens** - No server-side sessions

---

## Monitoring Points

1. **API Health:** GET /health
2. **Database Connection:** MongoDB ping
3. **AI Components:** Initialization status
4. **Token Validation:** Success/failure rates
5. **Response Times:** Per endpoint metrics

---

This architecture provides:
✅ Secure authentication
✅ Role-based authorization
✅ Scalable design
✅ AI integration
✅ Database persistence
✅ Easy deployment
