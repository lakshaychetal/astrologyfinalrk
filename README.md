
# 🌟 AstroAirk - Vedic Astrology AI API

Production-ready REST API for analyzing Vedic astrology birth charts using advanced RAG (Retrieval-Augmented Generation) with classical texts.

## 🚀 Features

- **🎯 REST API Architecture** - Pure backend API for frontend integration
- **📚 Classical Knowledge Base** - 351+ passages from authentic Vedic texts (BPHS, Phaladeepika, Brihat Jataka, Light on Life)
- **🤖 Dual AI System** - OpenRouter GPT-4o Mini + Gemini 2.0 Flash fallback
- **⚡ High Performance** - Draft answers in 1.5-2s, Expanded in 4-6s
- **💾 Smart Caching** - Session-based caching, 50-200ms cache hits
- **🌐 Multi-Niche Support** - Love, Career, Health, Wealth, Spiritual guidance
- **☁️ Cloud-Ready** - Google Cloud Run deployment included
- **� Rich Metadata** - Performance metrics, sources, complexity analysis

## 📚 Documentation

- **[Quick Start Guide](README_API.md)** - Get started in 5 minutes
- **[API Documentation](API_DOCUMENTATION.md)** - Complete endpoint reference
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment (Cloud Run, Docker, VPS)

## 🏃 Quick Start - Local Development

### Prerequisites
- Python 3.9+
- Google Cloud project with Vertex AI enabled
- RAG Corpus ID: `3379951520341557248`
- OpenRouter API Key (for GPT-4o Mini)

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd astroairk

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your keys:
#   OPENROUTER_API_KEY=sk-or-v1-...
#   GCP_PROJECT_ID=your-project-id
#   RAG_CORPUS_ID=3379951520341557248
```

### Run the API

```bash
# Start the FastAPI server
python api_main.py

# Server will start on http://localhost:8080
# Interactive docs: http://localhost:8080/docs
# OpenAPI schema: http://localhost:8080/openapi.json
```

### Test the API

```bash
# Run test suite
python test_api.py

# Or test manually:
curl http://localhost:8080/health
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/session/init` | POST | Initialize session with chart data |
| `/api/v1/session/{id}/status` | GET | Check session cache status |
| `/api/v1/query` | POST | Ask question (draft/expand modes) |
| `/api/v1/query/expand` | POST | Expand previous answer |
| `/api/v1/session/{id}` | DELETE | Delete session |
| `/api/v1/niches` | GET | List available niches |
| `/` | GET | Root endpoint |

**See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete details**

## 🎯 Example Usage

### Initialize Session
```bash
curl -X POST http://localhost:8080/api/v1/session/init \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "niche": "love",
    "chart_data": {
      "birth_time": "1990-01-01 10:30:00",
      "birth_place": "Mumbai, India",
      "chart_json": { ... }
    }
  }'
```

### Ask Question
```bash
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "When will I get married?",
    "mode": "draft"
  }'
```

## 🌐 Frontend Integration

### JavaScript Example
```javascript
// Initialize session
const initResponse = await fetch('http://localhost:8080/api/v1/session/init', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user123',
    niche: 'love',
    chart_data: { /* birth chart data */ }
  })
});
const { session_id } = await initResponse.json();

// Ask question
const queryResponse = await fetch('http://localhost:8080/api/v1/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session_id,
    question: 'When will I get married?',
    mode: 'draft'
  })
});
const result = await queryResponse.json();
console.log(result.answer);
```

**See [README_API.md](README_API.md) for React/Vue/Angular examples**

## ☁️ Production Deployment

### Option 1: Google Cloud Run (Recommended)

```bash
# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Or deploy directly
gcloud run deploy astroairk-api \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated
```

**See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide**

### Option 2: Docker

```bash
# Build image
docker build -t astroairk-api .

# Run container
docker run -p 8080:8080 --env-file .env astroairk-api
```

### Option 3: VPS (DigitalOcean, AWS EC2, etc.)

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn api_main:app --host 0.0.0.0 --port 8080

# Or use systemd for production
# See DEPLOYMENT.md for setup
```

## ⚙️ Configuration

Key environment variables in `.env`:

```bash
# OpenRouter API (Primary LLM)
OPENROUTER_API_KEY=sk-or-v1-...

# Google Cloud (RAG Corpus)
GCP_PROJECT_ID=your-project-id
GCP_REGION=asia-south1
RAG_CORPUS_ID=3379951520341557248

# Model Configuration
MODEL_NAME=openai/gpt-4o-mini
TEMPERATURE=0.2
MAX_OUTPUT_TOKENS=8192
```

**See `.env.example` for complete configuration options**

## 📊 Performance Benchmarks

| Operation | Latency | Notes |
|-----------|---------|-------|
| Draft Answer | 1.5-2s | Initial response |
| Expanded Answer | 4-6s | Detailed analysis |
| Cache Hit | 50-200ms | Subsequent queries |
| Session Init | 2-5s | First-time chart parsing |

## 🎓 Supported Niches

| Niche | Focus Areas |
|-------|-------------|
| **Love** | Relationships, marriage timing, compatibility |
| **Career** | Professional growth, job changes, success periods |
| **Health** | Physical wellbeing, health timing, remedies |
| **Wealth** | Financial gains, investments, prosperity |
| **Spiritual** | Moksha, meditation, spiritual evolution |

## 🔧 Development


### Project Structure

```
astroairk/
├── api_main.py                 # 🚀 FastAPI server (main entry point)
├── main_gradio_backup.py       # 💾 Original Gradio UI (backup)
├── config.py                   # ⚙️ Central configuration
├── niche_config.py            # 📚 Niche-specific instructions
├── requirements.txt           # 📦 Python dependencies
├── Dockerfile                 # 🐳 Container configuration
├── cloudbuild.yaml            # ☁️ Cloud Build configuration
├── .env.example               # 🔑 Environment template
│
├── agents/                    # 🤖 AI Agents
│   ├── smart_orchestrator.py      # Main orchestration logic
│   ├── real_rag_retriever.py      # RAG retrieval (Vertex AI)
│   ├── modern_synthesizer.py      # Answer synthesis
│   ├── simple_chart_parser.py     # Birth chart parsing
│   ├── cached_retriever.py        # Caching layer
│   └── ...
│
├── niche_instructions/        # 📖 Domain Knowledge
│   ├── love.py                    # Love/relationship guidance
│   ├── career.py                  # Career guidance
│   ├── health.py                  # Health guidance
│   └── ...
│
├── utils/                     # 🛠️ Utilities
│   ├── cache_manager.py           # Cache management
│   └── conversation_manager.py    # Session management
│
└── Documentation/             # 📚 Guides
    ├── README_API.md              # Quick start guide
    ├── API_DOCUMENTATION.md       # Complete API reference
    ├── DEPLOYMENT.md              # Deployment guide
    └── EMBEDDING_FIX_SUMMARY.md   # Technical details
```

### Running Tests

```bash
# Test API endpoints
python test_api.py

# Test specific queries
python test_love_queries.py

# Test RAG retrieval
python test_rag.py
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

## 🐛 Troubleshooting
