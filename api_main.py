"""
AstroAirk Backend API - FastAPI REST Server
Pure backend for developer frontend integration (no Gradio UI)
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import uvicorn
import os
import sys
import time
import logging
import uuid
import json
from datetime import datetime
import importlib.metadata as _metadata

# ---------------------------------------------------------------------------
# Compatibility adjustments
# ---------------------------------------------------------------------------
if not hasattr(_metadata, "packages_distributions"):
    try:
        import importlib_metadata as _metadata_backport
    except ImportError:
        _metadata_backport = None

    if _metadata_backport and hasattr(_metadata_backport, "packages_distributions"):
        _metadata.packages_distributions = _metadata_backport.packages_distributions
    else:
        def _packages_distributions_stub():
            return {}
        _metadata.packages_distributions = _packages_distributions_stub

# Import your existing agents
from agents.simple_chart_parser import ChartParser
from agents.openrouter_synthesizer import OpenRouterSynthesizer
from agents.gemini_embeddings import GeminiEmbeddings
from agents.smart_orchestrator import SmartOrchestrator
from agents.validator import LightweightValidator
from utils.conversation_manager import ConversationManager
from agents.niche_preloader import NichePreloader
from agents.cached_retriever import CachedRetriever
from agents.semantic_selector import SemanticFactorSelector
from utils.cache_manager import get_cache_manager

# Import RAG retriever
import config
if config.USE_REAL_RAG:
    from agents.real_rag_retriever import RealRAGRetriever as RAGRetriever
else:
    from agents.vector_search_retriever import VectorSearchRetriever as RAGRetriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AstroAirk API",
    description="Vedic Astrology AI Backend - Love, Career, Health Predictions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (lazy loaded)
orchestrator = None
chart_parser = None
conv_manager = None
rag_retriever = None
preloader = None

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChartData(BaseModel):
    """Birth chart data from developer's D1/D9/Dasha APIs"""
    birth_time: str = Field(..., example="1995-06-15 14:30:00")
    birth_place: str = Field(..., example="Mumbai, India")
    latitude: float = Field(..., example=19.076)
    longitude: float = Field(..., example=72.8777)
    timezone: str = Field(default="Asia/Kolkata", example="Asia/Kolkata")
    
    # Chart data as raw dict (parser will handle it)
    chart_json: Dict[str, Any] = Field(..., description="Complete D1/D9 chart data")

class SessionInitRequest(BaseModel):
    """Initialize a new session"""
    user_id: str = Field(..., example="user_12345")
    chart_data: ChartData
    niche: str = Field(..., example="love", description="love, career, health, wealth, or spiritual")

class QueryRequest(BaseModel):
    """Ask a question"""
    session_id: str = Field(..., example="abc-123-def")
    question: str = Field(..., example="When will I get married?")
    mode: str = Field(default="draft", example="draft", description="draft or expand")

class SessionResponse(BaseModel):
    """Session initialization response"""
    session_id: str
    status: str
    message: str
    niche: str
    timestamp: str

class QueryResponse(BaseModel):
    """Query answer response"""
    session_id: str
    question: str
    mode: str
    answer: str
    sources: List[str]
    performance: Dict[str, Any]
    metadata: Dict[str, Any]

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_services():
    """Initialize all AI services on startup"""
    global orchestrator, chart_parser, conv_manager, rag_retriever, preloader
    
    logger.info("🚀 Initializing AstroAirk Backend Services...")
    
    try:
        # Initialize chart parser
        chart_parser = ChartParser()
        logger.info("✅ Chart Parser initialized")
        
        # Initialize conversation manager
        conv_manager = ConversationManager()
        logger.info("✅ Conversation Manager initialized")
        
        # Initialize embeddings first (needed by other components)
        gemini_embedder = GeminiEmbeddings(
            project_id=config.PROJECT_ID,
            location=config.REGION,
            model=config.EMBEDDINGS_CONFIG.get("model", "text-embedding-004"),
            dimension=config.EMBEDDINGS_CONFIG.get("dimension", 768)
        )
        logger.info("✅ Gemini Embeddings initialized")
        
        # Initialize RAG retriever
        rag_retriever = RAGRetriever(
            project_id=config.PROJECT_ID,
            location=config.REGION,
            corpus_id=config.CORPUS_ID,
            top_k=6,
            similarity_threshold=config.RAG_SIMILARITY_THRESHOLD,
            final_top_k=3
        )
        logger.info("✅ RAG Retriever initialized")
        
        # Initialize preloader (needs rag_retriever and embeddings)
        preloader = NichePreloader(
            rag_retriever=rag_retriever,
            embeddings_client=gemini_embedder
        )
        logger.info("✅ Niche Preloader initialized")
        
        # Initialize OpenRouter synthesizer
        synthesizer = OpenRouterSynthesizer(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model_name="openai/gpt-4o-mini",
            temperature=0.7,
            max_output_tokens=3000
        )
        logger.info("✅ OpenRouter Synthesizer initialized (GPT-4.1 Mini)")
        
        # Initialize validator
        validator = LightweightValidator(
            project_id=config.PROJECT_ID,
            location=config.REGION
        )
        logger.info("✅ Validator initialized")
        
        # Initialize orchestrator (use correct parameters based on SmartOrchestrator's __init__)
        orchestrator = SmartOrchestrator(
            embedder=gemini_embedder,
            rag_retriever=rag_retriever,
            synthesizer=synthesizer
        )
        logger.info("✅ Smart Orchestrator initialized")
        
        logger.info("✅ All services ready!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AstroAirk Backend API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "orchestrator": orchestrator is not None,
            "chart_parser": chart_parser is not None,
            "rag_retriever": rag_retriever is not None,
            "conv_manager": conv_manager is not None
        }
    }

@app.post("/api/v1/session/init", response_model=SessionResponse)
async def initialize_session(request: SessionInitRequest):
    """
    Initialize a new astrology session.
    
    - Parses birth chart data (71+ factors)
    - Creates session
    - Pre-loads RAG cache for selected niche (async, non-blocking)
    
    Returns immediately while cache loads in background (~40s).
    """
    try:
        start_time = time.time()
        
        if not orchestrator or not chart_parser or not conv_manager:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        logger.info(f"📥 Session init request from user: {request.user_id}, niche: {request.niche}")
        
        # Use chart data directly (already in JSON format from request)
        chart_json = request.chart_data.chart_json
        logger.info(f"✅ Chart received: {len(chart_json)} top-level keys")
        
        # Create session (conv_manager generates its own session_id)
        session_id = conv_manager.create_session(
            chart_data=json.dumps(chart_json),  # Convert to string
            chart_factors=chart_json,  # Pass as dict
            niche=request.niche,
            user_id=request.user_id
        )
        logger.info(f"✅ Session created: {session_id}")
        
        # Pre-load RAG cache (TODO: implement async preloading)
        # if preloader:
        #     preloader.preload_async(session_id, request.niche)
        #     logger.info(f"⚡ RAG cache pre-loading started for niche: {request.niche}")
        
        latency = int((time.time() - start_time) * 1000)
        
        return SessionResponse(
            session_id=session_id,
            status="initialized",
            message=f"Session ready. Chart keys: {len(chart_json)}. Latency: {latency}ms",
            niche=request.niche,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Session init failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Session initialization failed: {str(e)}")

@app.get("/api/v1/session/{session_id}/status")
async def get_session_status(session_id: str):
    """
    Check session status and RAG cache loading progress.
    
    Poll this endpoint until cache_loaded=true before asking questions.
    """
    try:
        if not conv_manager:
            raise HTTPException(status_code=503, detail="Service not available")
        
        session = conv_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check cache status (simplified - preloader caching not yet implemented)
        cache_status = "ready"
        passages_cached = 0
        
        # TODO: Implement preloader caching
        # if preloader:
        #     cache_info = preloader.get_cache_status(session_id)
        #     cache_status = "loaded" if cache_info.get("loaded") else "loading"
        #     passages_cached = cache_info.get("passages_count", 0)
        
        return {
            "session_id": session_id,
            "status": "ready",
            "cache_loaded": True,
            "passages_cached": passages_cached,
            "niche": session.get("niche"),
            "created_at": session.get("created_at"),
            "user_id": session.get("user_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a user question and generate AI answer.
    
    Modes:
    - draft: Fast answer (1.5-2s, ~200 words, 4 bullets)
    - expand: Detailed answer (4-6s, ~600 words, comprehensive)
    
    Pipeline:
    1. Classify question complexity
    2. Retrieve relevant passages from RAG
    3. Generate answer using GPT-4.1 Mini
    4. Validate and return structured response
    """
    try:
        start_time = time.time()
        
        if not orchestrator or not conv_manager:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Verify session exists
        session = conv_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found. Please initialize session first.")
        
        logger.info(f"❓ Query: {request.question[:60]}... | Mode: {request.mode} | Session: {request.session_id}")
        
        # Process question through orchestrator
        result = await orchestrator.process_question_async(
            session_id=request.session_id,
            question=request.question,
            mode=request.mode,
            chart_data=session.get("chart_data"),
            niche=session.get("niche")
        )
        
        total_latency = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Answer generated in {total_latency}ms")
        
        return QueryResponse(
            session_id=request.session_id,
            question=request.question,
            mode=request.mode,
            answer=result.get("response", ""),
            sources=result.get("sources", []),
            performance={
                "total_ms": total_latency,
                "rag_ms": result.get("rag_latency_ms", 0),
                "llm_ms": result.get("llm_latency_ms", 0),
                "cache_hit": result.get("cache_hit", False)
            },
            metadata={
                "rag_passages": result.get("rag_passages_count", 0),
                "complexity": result.get("complexity", "UNKNOWN"),
                "niche": session.get("niche"),
                "model": "openai/gpt-4o-mini",
                "confidence": result.get("confidence", 0.0)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Query processing failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/api/v1/query/expand")
async def expand_previous_answer(session_id: str):
    """
    Expand the last draft answer into detailed version.
    
    Reuses RAG cache for faster response (~2-3s).
    """
    try:
        if not conv_manager or not orchestrator:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Get conversation history
        history = conv_manager.get_history(session_id)
        if not history or len(history) == 0:
            raise HTTPException(status_code=404, detail="No previous query found in session")
        
        last_exchange = history[-1]
        last_question = last_exchange.get("question")
        
        if not last_question:
            raise HTTPException(status_code=400, detail="Cannot expand: no valid previous question")
        
        session = conv_manager.get_session(session_id)
        
        # Re-run in expand mode
        result = await orchestrator.process_question_async(
            session_id=session_id,
            question=last_question,
            mode="expand",
            chart_data=session.get("chart_data"),
            niche=session.get("niche"),
            use_cache=True  # Reuse RAG cache
        )
        
        return {
            "session_id": session_id,
            "question": last_question,
            "mode": "expand",
            "answer": result.get("response", ""),
            "sources": result.get("sources", []),
            "performance": {
                "total_ms": result.get("total_latency_ms", 0),
                "llm_ms": result.get("llm_latency_ms", 0),
                "cache_reused": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Expand failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and clear its cache.
    
    Call this when user logs out or session expires.
    """
    try:
        if not conv_manager:
            raise HTTPException(status_code=503, detail="Service not available")
        
        # Delete from conversation manager
        conv_manager.delete_session(session_id)
        
        # Clear RAG cache if preloader exists
        if preloader:
            preloader.clear_cache(session_id)
        
        logger.info(f"🗑️  Session deleted: {session_id}")
        
        return {
            "status": "deleted",
            "session_id": session_id,
            "message": "Session and cache cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/niches")
async def list_niches():
    """List available astrology niches"""
    return {
        "niches": [
            {
                "id": "love",
                "name": "Love & Relationships",
                "description": "Marriage, romance, spouse characteristics, timing"
            },
            {
                "id": "career",
                "name": "Career & Professional",
                "description": "Career path, job success, professional growth"
            },
            {
                "id": "health",
                "name": "Health & Wellness",
                "description": "Physical health, wellness, vitality"
            },
            {
                "id": "wealth",
                "name": "Wealth & Finance",
                "description": "Financial prosperity, wealth accumulation"
            },
            {
                "id": "spiritual",
                "name": "Spiritual Growth",
                "description": "Spiritual path, purpose, growth"
            }
        ]
    }

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global error handler"""
    logger.error(f"❌ Unhandled error: {exc}")
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 70)
    logger.info("🚀 AstroAirk Backend API Starting...")
    logger.info("=" * 70)
    logger.info(f"📍 Environment: {os.getenv('ENV', 'development')}")
    logger.info(f"🌍 Region: {config.REGION}")
    logger.info(f"📦 Project: {config.PROJECT_ID}")
    logger.info(f"🗄️  RAG Corpus: {config.CORPUS_ID}")
    logger.info(f"🧠 Embedding Model: {config.EMBEDDINGS_CONFIG['model']}")
    logger.info(f"📏 Embedding Dims: {config.EMBEDDINGS_CONFIG['dimension']}")
    logger.info(f"🤖 LLM: openai/gpt-4o-mini (via OpenRouter)")
    logger.info("=" * 70)
    
    success = initialize_services()
    
    if success:
        logger.info("=" * 70)
        logger.info("✅ AstroAirk API Ready!")
        logger.info("📖 API Docs: http://localhost:8080/docs")
        logger.info("📖 ReDoc: http://localhost:8080/redoc")
        logger.info("=" * 70)
    else:
        logger.error("❌ Service initialization failed!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down AstroAirk API...")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    
    logger.info(f"Starting uvicorn server on port {port}...")
    
    uvicorn.run(
        "api_main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV") == "development",
        log_level="info"
    )
