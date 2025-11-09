# AstroAirk Backend API

Pure FastAPI backend for Vedic astrology predictions. **No Gradio UI** - designed for seamless frontend integration.

## 🎯 For Developers

This repository provides a ready-to-use REST API backend. Your frontend can call these endpoints to get AI-powered astrology predictions.

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd astroairk

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials:
# - GCP_PROJECT_ID=your-project-id
# - GCP_REGION=asia-south1
# - RAG_CORPUS_ID=your-corpus-id
# - OPENROUTER_API_KEY=your-openrouter-key
# - GOOGLE_CLOUD_API_KEY=your-gcp-key
```

### 3. Run Locally

```bash
python api_main.py
```

**API Available At:** `http://localhost:8080`

**Interactive Docs:** `http://localhost:8080/docs`

---

## 📖 API Documentation

**Complete API Reference:** See [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md)

### Quick Overview

| Endpoint | Method | Purpose | Latency |
|----------|--------|---------|---------|
| `/health` | GET | Health check | 10ms |
| `/api/v1/session/init` | POST | Create session | 100-200ms |
| `/api/v1/session/{id}/status` | GET | Check cache status | 20ms |
| `/api/v1/query` | POST | Ask question (draft) | 1.5-2s |
| `/api/v1/query` | POST | Ask question (expand) | 4-6s |
| `/api/v1/query/expand` | POST | Expand last answer | 2-3s |
| `/api/v1/session/{id}` | DELETE | Delete session | 50ms |
| `/api/v1/niches` | GET | List niches | 10ms |

---

## 🔄 Integration Flow

```
Your Frontend
    ↓
1. User enters birth details
    ↓
2. Call your D1/D9/Dasha calculation APIs
    ↓
3. POST /api/v1/session/init with chart data
    ← session_id
    ↓
4. [Optional] Poll GET /session/{id}/status until cache_loaded=true
    ↓
5. User asks question
    ↓
6. POST /api/v1/query (mode=draft)
    ← Answer in 1.5-2 seconds
    ↓
7. Show answer to user
    ↓
8. [Optional] User clicks "Show Details"
    ↓
9. POST /api/v1/query/expand
    ← Detailed answer in 2-3 seconds
    ↓
10. DELETE /api/v1/session/{id} on logout
```

---

## 🏗️ Architecture

```
Frontend (Your Code)
    ↓ HTTP/JSON
FastAPI REST API (This Repo)
    ↓
├── Chart Parser → Extracts 71+ astrological factors
├── RAG Retriever → Fetches relevant passages from classical texts
│   ├── Vertex AI RAG (351 passages)
│   └── Embedding: text-multilingual-embedding-002 @ 768-dim
└── LLM Synthesizer → GPT-4.1 Mini via OpenRouter
    └── Generates final answer with classical citations
```

---

## 🧪 Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:8080/health

# Initialize session
curl -X POST http://localhost:8080/api/v1/session/init \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "niche": "love",
    "chart_data": {
      "birth_time": "1995-06-15 14:30:00",
      "birth_place": "Mumbai",
      "latitude": 19.076,
      "longitude": 72.8777,
      "timezone": "Asia/Kolkata",
      "chart_json": {
        "planets": {...},
        "houses": {...}
      }
    }
  }'

# Ask question
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id-from-above",
    "question": "When will I get married?",
    "mode": "draft"
  }'
```

### Using Interactive Docs

1. Start the API: `python api_main.py`
2. Visit: `http://localhost:8080/docs`
3. Try out endpoints directly in browser!

---

## 🚀 Deployment

### Option 1: Google Cloud Run (Recommended)

```bash
# Deploy to Cloud Run
gcloud run deploy astroairk-api \
  --source . \
  --region asia-south1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300s \
  --allow-unauthenticated

# Your API will be available at:
# https://astroairk-api-xxx-asia-south1.run.app
```

### Option 2: Docker

```bash
# Build image
docker build -t astroairk-api .

# Run container
docker run -p 8080:8080 \
  --env-file .env \
  astroairk-api

# API available at: http://localhost:8080
```

### Option 3: Any VPS

```bash
# Install dependencies
pip install -r requirements.txt

# Run with production server
uvicorn api_main:app --host 0.0.0.0 --port 8080 --workers 4
```

---

## 📦 What's Inside

### Core Files

- **`api_main.py`** - FastAPI server (main entry point)
- **`config.py`** - Configuration settings
- **`.env`** - Environment variables (API keys, etc.)
- **`requirements.txt`** - Python dependencies

### Agents (AI Components)

- `agents/smart_orchestrator.py` - Main AI orchestrator
- `agents/simple_chart_parser.py` - Birth chart parser (71+ factors)
- `agents/real_rag_retriever.py` - RAG passage retrieval
- `agents/openrouter_synthesizer.py` - GPT-4.1 Mini synthesis
- `agents/gemini_embeddings.py` - Text embeddings
- `agents/niche_preloader.py` - RAG cache preloader
- `agents/cached_retriever.py` - Cached retrieval
- `agents/semantic_selector.py` - Factor selection

### Utilities

- `utils/conversation_manager.py` - Session management
- `utils/cache_manager.py` - Redis caching

### Niche Instructions

- `niche_instructions/love.py` - Love/relationship prompts
- `niche_instructions/career.py` - Career prompts
- `niche_instructions/health.py` - Health prompts
- `niche_instructions/wealth.py` - Wealth prompts
- `niche_instructions/spiritual.py` - Spiritual prompts

---

## 🎨 Response Format

### Draft Mode (Fast - 1.5-2s)

```json
{
  "answer": "• Bullet 1\n• Bullet 2\n• Bullet 3\n• Bullet 4\n\nSOURCES: [P_567], [P_891]",
  "sources": ["P_567", "P_891"],
  "performance": {
    "total_ms": 1850,
    "rag_ms": 620,
    "llm_ms": 1200
  }
}
```

**Output:**
- ~200 words
- 4 concise bullets
- Classical citations
- Actionable insights

### Expand Mode (Detailed - 4-6s)

```json
{
  "answer": "... 500-600 word detailed analysis ...",
  "sources": ["P_567", "P_891", "P_234", "P_445"],
  "performance": {
    "total_ms": 5200,
    "rag_ms": 1800,
    "llm_ms": 3400
  }
}
```

**Output:**
- ~500-600 words
- Comprehensive analysis
- Multiple aspects
- Detailed classical interpretations
- More sources

---

## 🎯 Supported Niches

| Niche ID | Name | Focus Area |
|----------|------|------------|
| `love` | Love & Relationships | Marriage timing, spouse characteristics, love life |
| `career` | Career & Professional | Career path, job success, professional growth |
| `health` | Health & Wellness | Physical health, wellness, vitality |
| `wealth` | Wealth & Finance | Financial prosperity, wealth accumulation |
| `spiritual` | Spiritual Growth | Spiritual path, purpose, life meaning |

---

## 📊 Performance

### Latency Targets

- **Session Init:** ~100-200ms
- **Draft Answer:** ~1.5-2 seconds
- **Expand Answer:** ~4-6 seconds
- **Expand Previous:** ~2-3 seconds (cache reuse)

### Cache Performance

- **First question:** Slower (cache miss, ~2s)
- **Subsequent questions:** Faster (cache hit, ~200ms RAG)
- **Cache size:** 300-400 passages per niche
- **Cache TTL:** 12 hours

---

## 🔐 Security Notes

### Current State (Development)
- ✅ CORS: Allow all
- ❌ Authentication: None
- ❌ Rate limiting: None

### Before Production
1. Add API key authentication
2. Whitelist CORS origins
3. Implement rate limiting (100 req/hour)
4. Add input validation
5. Set request size limits

See `API_DOCUMENTATION.md` for security implementation details.

---

## 🐛 Troubleshooting

### Common Issues

**1. "Services not initialized" (503 error)**
```bash
# Check logs for initialization errors
# Ensure .env has all required keys
# Verify GCP credentials are valid
```

**2. "Session not found" (404 error)**
```bash
# Session expired (24hr TTL)
# Or session_id is invalid
# Create new session with /api/v1/session/init
```

**3. Slow responses (>10s)**
```bash
# Check if RAG cache is loaded
# GET /api/v1/session/{id}/status
# Wait for cache_loaded=true
```

**4. "ModuleNotFoundError"**
```bash
# Install dependencies
pip install -r requirements.txt

# Or reinstall everything
pip install --force-reinstall -r requirements.txt
```

---

## 📞 Support

- **Interactive Docs:** Visit `/docs` for endpoint testing
- **API Reference:** See `API_DOCUMENTATION.md`
- **Issues:** GitHub repository issues
- **Contact:** Repository owner

---

## 🔄 Migration from Gradio

### What Changed

**Removed:**
- ❌ Gradio UI (`main.py`)
- ❌ Gradio dependencies

**Added:**
- ✅ FastAPI REST API (`api_main.py`)
- ✅ 8 REST endpoints
- ✅ JSON request/response
- ✅ OpenAPI docs (`/docs`)
- ✅ Session management
- ✅ Developer-friendly structure

### Old vs New

**Old (Gradio):**
```python
# Web UI with chat interface
python main.py
# Visit: http://localhost:8080 (web page)
```

**New (FastAPI):**
```python
# REST API server
python api_main.py
# Call: http://localhost:8080/api/v1/query (JSON API)
```

---

## 📝 Example Integration (JavaScript)

```javascript
// Initialize session
const initResponse = await fetch('http://localhost:8080/api/v1/session/init', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_id: 'user_123',
    niche: 'love',
    chart_data: {
      birth_time: '1995-06-15 14:30:00',
      birth_place: 'Mumbai',
      latitude: 19.076,
      longitude: 72.8777,
      timezone: 'Asia/Kolkata',
      chart_json: chartDataFromYourAPI
    }
  })
});

const {session_id} = await initResponse.json();

// Ask question
const queryResponse = await fetch('http://localhost:8080/api/v1/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id: session_id,
    question: 'When will I get married?',
    mode: 'draft'
  })
});

const {answer, sources} = await queryResponse.json();
console.log(answer); // Display to user
```

---

## ✨ Key Features

- ✅ **RESTful API** - Standard HTTP/JSON endpoints
- ✅ **Fast Performance** - Draft mode in ~2s, expand in ~4-6s
- ✅ **Smart Caching** - RAG cache for 50ms retrieval
- ✅ **Multi-Niche** - Love, career, health, wealth, spiritual
- ✅ **Classical Sources** - BPHS, Brihat Jataka citations
- ✅ **Production Ready** - Docker, Cloud Run support
- ✅ **Well Documented** - OpenAPI, examples, tutorials
- ✅ **Developer Friendly** - Clean code, type hints, logs

---

## 📚 Documentation

1. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference
2. **`/docs`** - Interactive Swagger UI
3. **`/redoc`** - Alternative ReDoc UI
4. **This README** - Quick start guide

---

## 🎓 License

[Add your license here]

---

## 👥 Contributors

[Add contributors]

---

**Ready to integrate? Start with** [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md) **for the complete guide!** 🚀
