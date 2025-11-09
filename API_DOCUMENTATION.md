# AstroAirk API Documentation

Complete REST API reference for integrating Vedic astrology predictions into your frontend.

**Version:** 1.0.0  
**Base URL (local):** `http://localhost:8080`  
**Base URL (production):** `https://your-cloud-run-url.run.app`

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
   - [Health Check](#get-health)
   - [List Niches](#get-apiv1niches)
   - [Initialize Session](#post-apiv1sessioninit)
   - [Session Status](#get-apiv1sessionidstatus)
   - [Ask Question](#post-apiv1query)
   - [Expand Answer](#post-apiv1queryexpand)
   - [Delete Session](#delete-apiv1sessionid)
3. [Data Models](#data-models)
4. [Error Handling](#error-handling)
5. [Rate Limits](#rate-limits)

---

## 🔐 Authentication

Currently **no authentication** required for testing.

**For Production:** Add API key header:
```http
Authorization: Bearer YOUR_API_KEY
```

---

## 📡 Endpoints

### GET `/health`

Health check endpoint to verify API is running.

**Request:**
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T10:30:00Z",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - API is healthy

---

### GET `/api/v1/niches`

List all available astrology niches.

**Request:**
```bash
curl http://localhost:8080/api/v1/niches
```

**Response:**
```json
{
  "niches": [
    {
      "id": "love",
      "name": "Love & Relationships",
      "description": "Marriage timing, spouse characteristics, relationship compatibility"
    },
    {
      "id": "career",
      "name": "Career & Business",
      "description": "Professional growth, job changes, business success"
    },
    {
      "id": "health",
      "name": "Health & Wellness",
      "description": "Physical wellbeing, health timing, remedies"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Success

---

### POST `/api/v1/session/init`

Initialize a new session with user's birth chart data.

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/session/init \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345",
    "niche": "love",
    "chart_data": {
      "birth_time": "1995-06-15 14:30:00",
      "birth_place": "Mumbai, India",
      "latitude": 19.076,
      "longitude": 72.8777,
      "timezone": "Asia/Kolkata",
      "chart_json": {
        "planets": {
          "Sun": {"sign": "Gemini", "house": 1, "degree": 24.5},
          "Moon": {"sign": "Aquarius", "house": 9, "degree": 18.2},
          "Venus": {"sign": "Cancer", "house": 2, "degree": 12.5},
          "Mars": {"sign": "Taurus", "house": 12, "degree": 8.3},
          "Jupiter": {"sign": "Scorpio", "house": 6, "degree": 22.1},
          "Saturn": {"sign": "Pisces", "house": 10, "degree": 28.9},
          "Mercury": {"sign": "Gemini", "house": 1, "degree": 15.7},
          "Rahu": {"sign": "Scorpio", "house": 6, "degree": 5.4},
          "Ketu": {"sign": "Taurus", "house": 12, "degree": 5.4}
        },
        "houses": {
          "1st_lord": "Mercury",
          "7th_lord": "Jupiter",
          "10th_lord": "Saturn"
        }
      }
    }
  }'
```

**Request Body:**
```typescript
{
  user_id: string;           // Unique user identifier
  niche: "love" | "career" | "health";
  chart_data: {
    birth_time: string;      // "YYYY-MM-DD HH:MM:SS"
    birth_place: string;     // "City, Country"
    latitude: number;        // Decimal degrees
    longitude: number;       // Decimal degrees
    timezone: string;        // IANA timezone
    chart_json: {
      planets: {             // All 9 planets + Asc
        [planet]: {
          sign: string;
          house: number;
          degree: number;
        }
      },
      houses: {              // House lords
        "1st_lord": string;
        "7th_lord": string;
        // ... etc
      }
    }
  }
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "initialized",
  "message": "Session created. Cache will be ready in 30-50 seconds.",
  "niche": "love",
  "cache_status": "loading"
}
```

**Status Codes:**
- `200 OK` - Session created successfully
- `422 Unprocessable Entity` - Invalid request data
- `500 Internal Server Error` - Server error

**Notes:**
- Session initialization is **fast** (100-200ms)
- Cache preloading happens in **background** (30-50s)
- You can start asking questions immediately (first answer may be slower)

---

### GET `/api/v1/session/{id}/status`

Check session cache status.

**Request:**
```bash
curl http://localhost:8080/api/v1/session/550e8400-e29b-41d4-a716-446655440000/status
```

**Response (Loading):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "cache_loaded": false,
  "passages_cached": 0,
  "message": "Cache is loading..."
}
```

**Response (Ready):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "cache_loaded": true,
  "passages_cached": 351,
  "message": "Cache ready. Fast responses enabled."
}
```

**Status Codes:**
- `200 OK` - Status retrieved
- `404 Not Found` - Session doesn't exist

**Polling Recommendation:**
Poll every 3-5 seconds until `cache_loaded: true` for optimal UX.

---

### POST `/api/v1/query`

Ask a question about the user's chart.

**Request (Draft Mode - Fast):**
```bash
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "When will I get married?",
    "mode": "draft"
  }'
```

**Request Body:**
```typescript
{
  session_id: string;           // From /session/init
  question: string;             // User's question
  mode: "draft" | "expand";     // draft=fast, expand=detailed
}
```

**Response:**
```json
{
  "question": "When will I get married?",
  "answer": "Based on your chart:\n\n• 7th lord Jupiter in 6th house suggests marriage after overcoming obstacles\n• Venus in 2nd house indicates focus on family values\n• Current dasha period shows favorable time in 2-3 years\n• Marriage likely between age 28-31\n\nClassical texts emphasize the importance of 7th house strength.",
  "mode": "draft",
  "sources": [
    "BPHS Chapter 78",
    "Phaladeepika Ch. 24",
    "Brihat Jataka - Marriage"
  ],
  "confidence": 0.87,
  "performance": {
    "total_ms": 1847,
    "rag_ms": 623,
    "llm_ms": 1224,
    "cache_hit": false
  },
  "metadata": {
    "rag_passages": 5,
    "complexity": "medium",
    "model": "openai/gpt-4o-mini",
    "niche": "love"
  }
}
```

**Request (Expand Mode - Detailed):**
```bash
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "When will I get married?",
    "mode": "expand"
  }'
```

**Response (Expand):**
```json
{
  "question": "When will I get married?",
  "answer": "# Detailed Marriage Analysis\n\n## Chart Indications\n\nYour 7th house (marriage) is ruled by Jupiter, which is positioned in the 6th house...\n\n[500-800 word detailed analysis]\n\n## Timing Analysis\n...\n\n## Recommendations\n...",
  "mode": "expand",
  "sources": [
    "BPHS Chapter 78 v12-15",
    "Phaladeepika Ch. 24 v8",
    "Brihat Jataka - Marriage Yoga"
  ],
  "confidence": 0.89,
  "performance": {
    "total_ms": 4521,
    "rag_ms": 0,
    "llm_ms": 4521,
    "cache_hit": true
  },
  "metadata": {
    "rag_passages": 0,
    "complexity": "medium",
    "model": "openai/gpt-4o-mini",
    "niche": "love"
  }
}
```

**Status Codes:**
- `200 OK` - Answer generated
- `404 Not Found` - Session doesn't exist
- `422 Unprocessable Entity` - Invalid request
- `500 Internal Server Error` - Generation failed

**Performance:**
- **Draft mode:** 1.5-2 seconds (4-5 bullet points)
- **Expand mode:** 4-6 seconds (detailed 500-800 words)
- **Cache hit:** 50-200ms (same question asked again)

---

### POST `/api/v1/query/expand`

**DEPRECATED:** Use `POST /api/v1/query` with `mode: "expand"` instead.

Shortcut endpoint to expand the previous answer.

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/query/expand \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

---

### DELETE `/api/v1/session/{id}`

Delete a session and free up resources.

**Request:**
```bash
curl -X DELETE http://localhost:8080/api/v1/session/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "status": "deleted",
  "message": "Session deleted successfully",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Codes:**
- `200 OK` - Session deleted
- `404 Not Found` - Session doesn't exist

**Notes:**
- Call this when user logs out
- Sessions auto-expire after 12 hours

---

## 📦 Data Models

### ChartData

```typescript
interface ChartData {
  birth_time: string;        // "YYYY-MM-DD HH:MM:SS"
  birth_place: string;       // "City, Country"
  latitude: number;          // Decimal degrees
  longitude: number;         // Decimal degrees
  timezone: string;          // "Asia/Kolkata"
  
  chart_json: {
    planets: {
      Sun: PlanetPosition;
      Moon: PlanetPosition;
      Mars: PlanetPosition;
      Mercury: PlanetPosition;
      Jupiter: PlanetPosition;
      Venus: PlanetPosition;
      Saturn: PlanetPosition;
      Rahu: PlanetPosition;
      Ketu: PlanetPosition;
      Ascendant?: PlanetPosition;
    };
    
    houses: {
      "1st_lord": string;
      "2nd_lord": string;
      "7th_lord": string;
      "10th_lord": string;
      // ... all 12 houses
    };
    
    // Optional but recommended
    d9_planets?: { [planet: string]: PlanetPosition };
    current_mahadasha?: string;
    current_antardasha?: string;
  }
}

interface PlanetPosition {
  sign: string;              // "Aries", "Taurus", etc.
  house: number;             // 1-12
  degree: number;            // 0-30
  retrograde?: boolean;      // Optional
  nakshatra?: string;        // Optional
}
```

### QueryResponse

```typescript
interface QueryResponse {
  question: string;
  answer: string;
  mode: "draft" | "expand";
  sources: string[];
  confidence: number;        // 0-1
  
  performance: {
    total_ms: number;
    rag_ms: number;
    llm_ms: number;
    cache_hit: boolean;
  };
  
  metadata: {
    rag_passages: number;
    complexity: "low" | "medium" | "high";
    model: string;
    niche: string;
  };
}
```

---

## ❌ Error Handling

### Error Response Format

```json
{
  "detail": "Error message here",
  "error_code": "SESSION_NOT_FOUND",
  "timestamp": "2025-11-09T10:30:00Z"
}
```

### Common Error Codes

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request body |
| 404 | `SESSION_NOT_FOUND` | Session ID doesn't exist |
| 422 | `VALIDATION_ERROR` | Invalid data format |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | API temporarily down |

### Example Error Handling (TypeScript)

```typescript
try {
  const response = await fetch('/api/v1/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id, question, mode: 'draft' })
  });
  
  if (!response.ok) {
    const error = await response.json();
    
    if (response.status === 404) {
      // Session expired - reinitialize
      await initializeNewSession();
    } else if (response.status === 429) {
      // Rate limited - show message
      showMessage("Too many requests. Please wait.");
    } else {
      // Other errors
      showError(error.detail);
    }
    return;
  }
  
  const data = await response.json();
  // Success!
  
} catch (error) {
  // Network error
  showError("Connection failed. Please check your internet.");
}
```

---

## 🚦 Rate Limits

**Current:** No rate limits (development)

**Recommended for Production:**
- 100 requests/hour per user
- 10 concurrent sessions per user
- 1000 requests/day per IP

**Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1636459200
```

---

## 🎯 Integration Flow

```
1. User fills birth form on your frontend
   ↓
2. Your frontend calls YOUR D1/D9/Dasha APIs
   ↓
3. Get chart data from your APIs
   ↓
4. POST /api/v1/session/init (with chart_data)
   → Get session_id
   ↓
5. (Optional) Poll GET /api/v1/session/{id}/status
   → Wait for cache_loaded: true
   ↓
6. User asks question
   ↓
7. POST /api/v1/query (mode: draft)
   → Show quick answer (1-2s)
   ↓
8. User clicks "Show More Details"
   ↓
9. POST /api/v1/query (mode: expand, same question)
   → Show detailed answer (4-6s)
   ↓
10. User logs out
    ↓
11. DELETE /api/v1/session/{id}
    → Cleanup
```

---

## 📊 Performance Expectations

| Operation | Latency | Notes |
|-----------|---------|-------|
| Session Init | 100-200ms | Returns immediately |
| Cache Preload | 30-50s | Background, non-blocking |
| Draft Answer (cold) | 2-3s | First query without cache |
| Draft Answer (warm) | 1-2s | With cache loaded |
| Expand Answer | 4-6s | Detailed analysis |
| Cache Hit | 50-200ms | Same question repeated |
| Session Status | 5-10ms | Instant |

---

## 🔐 Security Best Practices

### For Production:

1. **Authentication:**
   ```typescript
   headers: {
     'Authorization': 'Bearer YOUR_API_KEY',
     'Content-Type': 'application/json'
   }
   ```

2. **CORS Whitelist:**
   Update `api_main.py`:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

3. **HTTPS Only:**
   Enforce HTTPS in production

4. **Input Validation:**
   Already handled by Pydantic

5. **Rate Limiting:**
   Implement per-user limits

---

## 🧪 Testing

### Interactive API Docs

Visit: `http://localhost:8080/docs`

### cURL Examples

See [README_API.md](README_API.md) for complete examples.

### Test Script

```bash
python test_api.py
```

---

## 📞 Support

- **Interactive Docs:** http://localhost:8080/docs
- **Redoc:** http://localhost:8080/redoc
- **Quick Start:** [README_API.md](README_API.md)
- **Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🚀 Quick Start

```bash
# 1. Start API
python api_main.py

# 2. Test health
curl http://localhost:8080/health

# 3. Initialize session
curl -X POST http://localhost:8080/api/v1/session/init \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","niche":"love","chart_data":{...}}'

# 4. Ask question
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"session_id":"xxx","question":"When will I get married?","mode":"draft"}'
```

---

**Ready to integrate? See [README_API.md](README_API.md) for complete integration guide!** 🚀
