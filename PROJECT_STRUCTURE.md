# AstroAirk - Project Structure

## 📁 Directory Organization

```
astroairk/
├── main.py                      # Application entry point (Gradio UI)
├── config.py                    # Configuration management
├── niche_config.py              # Niche-specific configurations
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (not in git)
├── .env.example                 # Example environment configuration
│
├── agents/                      # Core AI agents
│   ├── __init__.py
│   ├── openrouter_synthesizer.py    # GPT-4.1 Mini final synthesis (PRIMARY)
│   ├── modern_synthesizer.py        # Gemini synthesis (fallback)
│   ├── smart_orchestrator.py        # Main orchestration logic
│   ├── simple_chart_parser.py       # Chart data parser
│   ├── question_complexity.py       # Question classifier
│   ├── semantic_selector.py         # Semantic factor selection
│   ├── cached_retriever.py          # Parallel RAG retrieval with caching
│   ├── real_rag_retriever.py        # Vertex AI RAG integration
│   ├── vector_search_retriever.py   # Vector search fallback
│   ├── niche_preloader.py           # Knowledge pre-loading system
│   ├── fast_reranker.py             # NumPy-based reranking (53x faster)
│   ├── gemini_embeddings.py         # Embedding generation
│   └── validator.py                 # Response validation
│
├── utils/                       # Utility modules
│   ├── __init__.py
│   ├── cache_manager.py             # Two-level caching system (Redis + in-memory)
│   └── conversation_manager.py      # Conversation session management
│
├── niche_instructions/          # Niche-specific prompts
│   ├── __init__.py
│   ├── love.py                      # Love & Relationships
│   ├── career.py                    # Career & Profession
│   ├── health.py                    # Health & Wellness
│   ├── wealth.py                    # Finance & Wealth
│   └── spiritual.py                 # Spiritual Growth
│
└── docs/                        # Documentation
    ├── README.md                    # Project overview
    └── QUICK_START.md               # Quick start guide
```

## 🧩 Core Components

### **1. Main Application** (`main.py`)
- Gradio web interface
- Session management
- Request routing
- Performance tracking

### **2. Synthesis Engine**
- **Primary:** OpenRouter GPT-4.1 Mini (1-2s draft, 3-5s detailed)
- **Fallback:** Gemini 2.5 Flash
- **Modes:** Draft (500 tokens) vs Expand (1500 tokens)

### **3. RAG Pipeline**
```
User Question
    ↓
Question Classifier (SIMPLE/MODERATE/COMPLEX)
    ↓
Semantic Factor Selector (chart highlights)
    ↓
Knowledge Pre-loader (351 passages cached)
    ↓
Parallel RAG Retrieval (6 passages)
    ↓
Fast NumPy Reranker (→ top 3)
    ↓
Final Synthesis (GPT-4.1 Mini)
    ↓
Response (with citations)
```

### **4. Caching System**
- **Level 1:** Intent + Chart bucket (hot intents, 24h TTL)
- **Level 2:** Full prompt cache (6h TTL)
- **Backend:** Redis (primary) + in-memory LRU (fallback)

## 🚀 Performance Characteristics

| Metric | Value |
|--------|-------|
| **Draft Response** | 1-2 seconds |
| **Detailed Response** | 3-5 seconds |
| **Cache Hit Rate** | 35-45% |
| **RAG Retrieval** | 650-900ms (merged query) |
| **Reranking** | 15ms (NumPy fast) |
| **Pre-load Time** | 37s (351 passages, 117 factors) |

## 📦 Dependencies

### Core Libraries
- `gradio` - Web UI framework
- `google-genai` - Vertex AI integration
- `requests` - HTTP client (for OpenRouter)
- `numpy` - Fast numerical operations
- `python-dotenv` - Environment management

### Google Cloud
- Vertex AI RAG API
- Gemini embeddings (text-embedding-004)
- Gemini models (fallback synthesis)

### Optional
- `redis` - Production caching (falls back to in-memory)

## 🔧 Configuration

### Environment Variables (`.env`)
```bash
# Google Cloud
GCP_PROJECT_ID=your-project-id
GCP_REGION=asia-south1
RAG_CORPUS_ID=your-corpus-id
GOOGLE_CLOUD_API_KEY=your-api-key

# OpenRouter (Primary Synthesis)
OPENROUTER_API_KEY=sk-or-v1-...

# Model Settings
MODEL_NAME=gemini-1.5-flash
TEMPERATURE=0.2
MAX_OUTPUT_TOKENS=2400

# RAG Settings
USE_REAL_RAG=true
RAG_TOP_K=6
RAG_SIMILARITY_THRESHOLD=0.5

# Server
PORT=8080
DEBUG=false
```

## 🎯 Key Features

### ✅ Implemented
1. **Two-pass generation** (Draft/Expand modes)
2. **Merged RAG queries** (4→1 call, 3.2x faster)
3. **Fast NumPy reranker** (53x faster than LLM)
4. **Two-level caching** (Redis + in-memory)
5. **Knowledge pre-loading** (351 passages cached)
6. **Semantic factor selection** (chart highlights)
7. **Comprehensive timing instrumentation**
8. **Session-based conversations**
9. **OpenRouter GPT-4.1 Mini integration** (primary synthesis)

### 🚧 Future Enhancements
1. Long-term conversational memory (5-message summarization)
2. Cross-session memory persistence
3. User profile memory
4. Answer cache with cross-user sharing
5. Passage cache pre-warming
6. Background summarization

## 📊 Code Quality

### Standards
- Type hints throughout
- Comprehensive logging
- Error handling with fallbacks
- Response caching
- Token budget management

### Testing
```bash
# Compile check
python -m compileall .

# RAG test
python test_rag.py

# Full system test
USE_REAL_RAG=true python main.py
```

## 🔒 Security

- API keys in `.env` (not in git)
- `.gitignore` for sensitive files
- Encrypted transit (TLS)
- Rate limiting (TODO)
- Input validation

## 📝 Development Workflow

1. **Setup:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env  # Edit with your keys
   ```

2. **Run:**
   ```bash
   USE_REAL_RAG=true python main.py
   ```

3. **Deploy:**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

## 💡 Architecture Highlights

### Why OpenRouter + GPT-4.1 Mini?
- **No thinking overhead** (unlike Gemini 2.5 Flash)
- **3x faster** token-to-token generation
- **46% cheaper** per token
- **Same quality** for Vedic astrology synthesis

### Why Two-Level Caching?
- **Level 1:** Reuses answers for similar intents (35% hit rate)
- **Level 2:** Reuses RAG passages (saves 700ms on hits)
- **Combined:** 30-40% average speedup

### Why Fast Reranker?
- **NumPy vectorization:** 53x faster than LLM reranking
- **15ms latency:** vs 800ms for LLM
- **Same quality:** Cosine + IDF + tag matching

## 🎓 Learning Resources

- [Vertex AI RAG](https://cloud.google.com/vertex-ai/docs/generative-ai/rag-overview)
- [OpenRouter API](https://openrouter.ai/docs)
- [Gradio Documentation](https://www.gradio.app/docs)

## 📞 Support

For issues or questions, check:
1. `README.md` - Project overview
2. `QUICK_START.md` - Quick start guide
3. This file - Project structure
