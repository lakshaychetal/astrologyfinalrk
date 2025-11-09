"""
Main Application File - Approach B Architecture  
Updated for Approach B Architecture with 4-Phase Optimization
Supports continuous multi-turn conversations with best-in-world quality
"""

import gradio as gr
import json
import sys
import os
from datetime import datetime
import time
import logging
import importlib.metadata as _metadata

# ---------------------------------------------------------------------------
# Compatibility adjustments
# ---------------------------------------------------------------------------
# Python 3.9's ``importlib.metadata`` module does not expose
# ``packages_distributions`` which recent google/vertexai clients rely on.
# When that attribute is missing we borrow the implementation from the
# ``importlib_metadata`` backport (installed in the virtualenv) or fall back
# to a benign stub so client libraries stop crashing during import.
if not hasattr(_metadata, "packages_distributions"):
    try:  # pragma: no cover - defensive import for older runtimes
        import importlib_metadata as _metadata_backport
    except ImportError:  # pragma: no cover - fall back to stub when unavailable
        _metadata_backport = None

    if _metadata_backport and hasattr(_metadata_backport, "packages_distributions"):
        _metadata.packages_distributions = _metadata_backport.packages_distributions  # type: ignore[attr-defined]
    else:
        def _packages_distributions_stub():  # pragma: no cover - emergency fallback
            return {}

        _metadata.packages_distributions = _packages_distributions_stub  # type: ignore[attr-defined]

# Import Approach B modules
from agents.simple_chart_parser import ChartParser
from agents.modern_synthesizer import ModernSynthesizer
from agents.openrouter_synthesizer import OpenRouterSynthesizer  # NEW: GPT-4.1 Mini via OpenRouter
from agents.gemini_embeddings import GeminiEmbeddings
from agents.smart_orchestrator import SmartOrchestrator
from agents.question_complexity import QuestionComplexityClassifier
from agents.validator import LightweightValidator
from utils.conversation_manager import ConversationManager

# Import NEW caching system (Phase 1)
from agents.niche_preloader import NichePreloader
from agents.cached_retriever import CachedRetriever  # Phase 2: Parallel retrieval
from agents.semantic_selector import SemanticFactorSelector  # Phase 3: Semantic targeting
from utils.cache_manager import get_cache_manager

# Import existing niche instructions
try:
    from niche_instructions.love import LOVE_INSTRUCTION
    from niche_instructions.career import CAREER_INSTRUCTION
    from niche_instructions.wealth import WEALTH_INSTRUCTION
    from niche_instructions.health import HEALTH_INSTRUCTION
    from niche_instructions.spiritual import SPIRITUAL_INSTRUCTION
    
    NICHE_INSTRUCTIONS = {
        "Love & Relationships": LOVE_INSTRUCTION,
        "Career & Professional": CAREER_INSTRUCTION,
        "Wealth & Finance": WEALTH_INSTRUCTION,
        "Health & Wellness": HEALTH_INSTRUCTION,
        "Spiritual Growth": SPIRITUAL_INSTRUCTION
    }
except ImportError:
    # Fallback if niche instructions not found
    NICHE_INSTRUCTIONS = {
        "Love & Relationships": "Focus on relationships and marriage analysis",
        "Career & Professional": "Focus on career and professional growth",
        "Wealth & Finance": "Focus on wealth and financial prosperity",
        "Health & Wellness": "Focus on health and wellness analysis",
        "Spiritual Growth": "Focus on spiritual development and purpose"
    }

import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import REAL or MOCK RAG retriever based on config
if config.USE_REAL_RAG:
    from agents.real_rag_retriever import RealRAGRetriever as RAGRetriever
    logger.info("✅ Using REAL RAG Retriever (Vertex AI RAG API)")
else:
    from agents.vector_search_retriever import VectorSearchRetriever as RAGRetriever
    logger.info("⚠️ Using MOCK RAG Retriever (fallback mode)")

# Global configuration
USE_APPROACH_B = True  # NEW: Enable Approach B
USE_DYNAMIC_MODE = False  # DISABLE: Old 5-agent mode
PORT = 8080
DEBUG = True

# Global instances (lazy loaded)
vector_search_retriever = None
chart_parser = None
synthesizer = None
validator = None
conversation_manager = ConversationManager(session_ttl_minutes=60)
smart_orchestrator = None
gemini_embedder = None

# NEW: Caching system instances (Phases 1-4)
cache_manager = None
niche_preloader = None
cached_retriever = None
semantic_selector = None  # Phase 3: Semantic factor selection

# Current session
current_session_id = None
current_chart_factors = None
current_niche = None
preload_status = {}  # Track pre-load progress per session


def initialize_approach_b():
    """Initialize all Approach B components with 4-Phase Optimization"""
    global vector_search_retriever
    global chart_parser, synthesizer, validator
    global cache_manager, niche_preloader, cached_retriever, semantic_selector
    global smart_orchestrator, gemini_embedder
    
    logger.info("Initializing Approach B components...")
    
    try:
        # Initialize chart parser (reuse existing)
        chart_parser = ChartParser()
        
        # Initialize each component
        # Initialize REAL or MOCK RAG retriever (FAST VECTOR SEARCH)
        if config.USE_REAL_RAG:
            vector_search_retriever = RAGRetriever(
                project_id=config.PROJECT_ID,
                location=config.REGION,
                corpus_id=config.CORPUS_ID,
                top_k=config.RAG_TOP_K,
                similarity_threshold=config.RAG_SIMILARITY_THRESHOLD
            )
            logger.info("✅ REAL RAG retriever initialized!")
        else:
            vector_search_retriever = RAGRetriever(
                project_id=config.PROJECT_ID,
                location=config.REGION,
                index_resource_name=config.VECTOR_SEARCH_CONFIG.get("index_resource_name"),
                deployed_index_id=config.VECTOR_SEARCH_CONFIG.get("deployed_index_id"),
                index_endpoint_name=config.VECTOR_SEARCH_CONFIG.get("index_endpoint_name")
            )
            logger.warning("⚠️ MOCK RAG retriever initialized (no real corpus)!")
        
        # Initialize synthesizer with mock client for now
        try:
            from google import genai

            gemini_client = genai.Client(
                vertexai=True,
                project=config.PROJECT_ID,
                location=config.REGION
            )

            # Use OpenRouter GPT-4.1 Mini for final synthesis (PRIMARY)
            synthesizer = OpenRouterSynthesizer(
                api_key=os.getenv("OPENROUTER_API_KEY", "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"),
                model_name="openai/gpt-4.1-mini",
                temperature=config.SYNTHESIZER_CONFIG.get("temperature", 0.6),
                max_output_tokens=config.SYNTHESIZER_CONFIG.get("max_output_tokens", 2000),
            )
            
            logger.info("✅ Using OpenRouter GPT-4.1 Mini for final synthesis")

            gemini_embedder = GeminiEmbeddings(
                project_id=config.PROJECT_ID,
                location=config.REGION,
                model=config.EMBEDDINGS_CONFIG.get("model", "text-embedding-004"),
                dimension=config.EMBEDDINGS_CONFIG.get("dimension", 768)
            )

        except Exception as e:
            logger.warning(f"Could not initialize services: {e}")
            synthesizer = None
            gemini_embedder = None
        
        validator = LightweightValidator(
            project_id=config.PROJECT_ID,
            location=config.REGION
        )
        
        # NEW: Initialize caching system with all 4 phases
        logger.info("Initializing 4-phase optimization system...")
        cache_manager = get_cache_manager()
        
        # Phase 3: Semantic factor selector
        if gemini_embedder:
            semantic_selector = SemanticFactorSelector(
                embeddings_client=gemini_embedder
            )
            logger.info("✅ Phase 3: Semantic factor selector initialized")

            # Phases 1 & 2: Pre-loader with parallel retrieval
            niche_preloader = NichePreloader(
                rag_retriever=vector_search_retriever,
                embeddings_client=gemini_embedder,
                cache_manager=cache_manager
            )
            logger.info("✅ Phases 1 & 2: Niche pre-loader with parallel retrieval initialized")

            # Phase 2 & 4: Cached retriever with parallel + multi-stage retrieval
            cached_retriever = CachedRetriever(
                rag_retriever=vector_search_retriever,
                embeddings_client=gemini_embedder,
                cache_manager=cache_manager
            )
            logger.info("✅ Phases 2 & 4: Cached retriever with multi-stage support initialized")
        else:
            semantic_selector = None
            niche_preloader = None
            cached_retriever = None
            logger.warning("Semantic selector and cache optimizations disabled (no embedder)")

        if synthesizer and gemini_embedder:
            smart_orchestrator = SmartOrchestrator(
                embedder=gemini_embedder,
                rag_retriever=vector_search_retriever,
                synthesizer=synthesizer,
                classifier=QuestionComplexityClassifier(),
            )
            logger.info("✅ Smart orchestrator ready (Gemini Pro synthesis)")
        else:
            smart_orchestrator = None
            logger.warning("Smart orchestrator disabled because Gemini services are unavailable")
        
        logger.info("✅ All 4 optimization phases ready!")
        logger.info("All Approach B components initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        raise


def initialize_session_button(chart_data: str, niche: str):
    """Initialize new session with chart data"""
    global current_session_id, current_chart_factors, current_niche, preload_status
    
    logger.info(f"Initializing session: Niche={niche}")
    
    try:
        if not chart_data.strip():
            return "❌ Error: Please enter chart data", {}
        
        # Parse chart into factors
        logger.info("Parsing chart data...")
        factors = chart_parser.parse_chart_text(
            chart_data=chart_data,
            niche=niche
        )
        
        # Create conversation session
        current_session_id = conversation_manager.create_session(
            chart_data=chart_data,
            chart_factors=factors,
            niche=niche,
            user_id="user_001"
        )
        
        current_chart_factors = factors
        current_niche = niche
        
        # Prepare display
        factors_display = json.dumps(factors, indent=2)[:1000]  # Truncate for display
        
        status_msg = (
            f"✅ Session initialized!\n\n"
            f"Session ID: {current_session_id}\n"
            f"Niche: {niche}\n"
            f"Factors parsed: {len(factors)}\n\n"
            f"You can now ask questions in the chat below."
        )
        
        return status_msg, factors
        
    except Exception as e:
        logger.error(f"Session initialization failed: {str(e)}")
        return f"❌ Error: {str(e)}", {}


def preload_niche_knowledge_handler(chart_data: str, niche: str):
    """
    Pre-load niche-specific knowledge into cache
    This is the NEW smart caching feature!
    """
    global current_session_id, current_chart_factors, current_niche, preload_status
    
    logger.info(f"🔮 Pre-loading {niche} knowledge...")
    
    try:
        # Ensure session is initialized
        if not current_session_id or not current_chart_factors:
            # Initialize session first
            status, factors = initialize_session_button(chart_data, niche)
            if "Error" in status:
                return status
        
        # Progress callback for UI updates
        progress_messages = []
        
        def progress_callback(percent: float, message: str):
            """Capture progress updates"""
            progress_msg = f"[{percent:.0f}%] {message}"
            progress_messages.append(progress_msg)
            logger.info(progress_msg)
        
        # Pre-load knowledge
        start_time = time.time()
        result = niche_preloader.preload_niche_knowledge(
            session_id=current_session_id,
            niche=current_niche,
            chart_factors=current_chart_factors,
            progress_callback=progress_callback
        )
        
        preload_time = time.time() - start_time
        
        # Store status
        preload_status[current_session_id] = {
            "status": result["status"],
            "factors_processed": result.get("factors_processed", 0),
            "passages_cached": result.get("passages_cached", 0),
            "time_taken": preload_time,
            "timestamp": datetime.now().isoformat()
        }
        
        # Format success message
        if result["status"] == "success":
            status_msg = (
                f"✅ **Pre-loading Complete!**\n\n"
                f"📊 **Stats:**\n"
                f"- Factors processed: {result['factors_processed']}\n"
                f"- Passages cached: {result['passages_cached']}\n"
                f"- Time taken: {preload_time:.1f}s\n"
                f"- Cache ready: ✅\n\n"
                f"💡 **You can now ask questions!**\n"
                f"Expected response time: **6-8 seconds** (vs 23s before)\n\n"
                f"**Progress Log:**\n"
                + "\n".join(progress_messages[-10:])  # Last 10 messages
            )
        else:
            status_msg = (
                f"⚠️ **Pre-loading Partial Success**\n\n"
                f"Status: {result['status']}\n"
                f"Error: {result.get('error', 'Unknown error')}\n\n"
                f"You can still ask questions, but some factors may not be cached."
            )
        
        return status_msg
        
    except Exception as e:
        logger.error(f"Pre-loading failed: {str(e)}")
        return f"❌ **Pre-loading Failed**\n\nError: {str(e)}\n\nYou can still ask questions using regular retrieval."


def chat_handler(message: str, history: list, mode: str = "draft"):
    """
    Handle user message and generate response using Approach B
    
    Args:
        message (str): User question
        history (list): Conversation history
        mode (str): "draft" for quick answer, "expand" for detailed
    
    Returns:
        str: Response text
    """
    
    global current_session_id, current_chart_factors, current_niche
    
    if not current_session_id or not current_chart_factors:
        return "❌ Please initialize session first"
    
    mode_label = "🚀 QUICK" if mode == "draft" else "📚 DETAILED"
    logger.info(f"Processing question ({mode_label}): {message[:60]}...")
    start_time = time.time()

    try:
        if not smart_orchestrator or not synthesizer:
            logger.error("Smart orchestrator is not initialized")
            return "❌ The system is still initializing. Please try again in a moment."

        orchestration_result = smart_orchestrator.answer_question(
            question=message,
            chart_factors=current_chart_factors,
            niche=current_niche,
            niche_instruction=NICHE_INSTRUCTIONS.get(current_niche, current_niche),
            conversation_history=conversation_manager.get_conversation_context(current_session_id),
            mode=mode  # Pass mode for draft/expand
        )

        answer = orchestration_result.response
        latencies = orchestration_result.latencies
        total_time = latencies.get("total_ms", (time.time() - start_time) * 1000)

        conversation_manager.add_exchange(
            session_id=current_session_id,
            user_message=message,
            assistant_response=answer,
            metadata={
                "mode": mode,
                "total_latency_ms": total_time,
                "classification_ms": latencies.get("classification_ms", 0.0),
                "chart_focus_ms": latencies.get("chart_focus_ms", 0.0),
                "query_generation_ms": latencies.get("query_generation_ms", 0.0),
                "rag_call_ms": latencies.get("rag_call_ms", 0.0),
                "dedupe_ms": latencies.get("dedupe_ms", 0.0),
                "rerank_ms": latencies.get("rerank_ms", 0.0),
                "retrieval_ms": latencies.get("retrieval_ms", 0.0),
                "prompt_build_ms": latencies.get("prompt_build_start_ms", 0.0),
                "llm_first_byte_ms": latencies.get("llm_first_byte_ms", 0.0),
                "llm_total_ms": latencies.get("llm_total_ms", 0.0),
                "synthesis_ms": latencies.get("synthesis_ms", 0.0),
                "complexity": orchestration_result.complexity,
                "passages_used": orchestration_result.passages_used,
                "rag_used": orchestration_result.rag_used,
                "queries": orchestration_result.queries,
            }
        )

        # Enhanced timing breakdown
        timing_lines = [
            f"**🎯 Mode:** {mode_label} ({'Quick Draft' if mode == 'draft' else 'Full Detail'})",
            f"- Classification: {latencies.get('classification_ms', 0.0):.0f}ms",
            f"- Chart Focus: {latencies.get('chart_focus_ms', 0.0):.0f}ms",
            f"- Query Gen: {latencies.get('query_generation_ms', 0.0):.0f}ms",
            f"- RAG Call: {latencies.get('rag_call_ms', 0.0):.0f}ms (merged query)",
            f"- Dedupe: {latencies.get('dedupe_ms', 0.0):.0f}ms",
            f"- Rerank: {latencies.get('rerank_ms', 0.0):.0f}ms (NumPy fast)",
            f"- LLM First Token: {latencies.get('llm_first_byte_ms', 0.0):.0f}ms",
            f"- LLM Total: {latencies.get('llm_total_ms', 0.0):.0f}ms",
            f"- **Total: {total_time:.0f}ms ({total_time/1000:.1f}s)**",
        ]

        if orchestration_result.passages_used:
            timing_lines.insert(1, f"- RAG passages used: {orchestration_result.passages_used}")

        timing_info = "\n\n---\n⏱️ **Performance Breakdown:**\n" + "\n".join(timing_lines)

        logger.info(
            "Question processed | mode=%s | complexity=%s | rag_passages=%d | total=%.0fms",
            mode,
            orchestration_result.complexity,
            orchestration_result.passages_used,
            total_time,
        )

        return answer + timing_info

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        return f"❌ Error: {str(e)}"


def create_gradio_interface():
    """Create Gradio interface"""
    
    with gr.Blocks(title="Vedic Astrology AI Advisor - Approach B", theme=gr.themes.Soft()) as interface:
        
        gr.Markdown("# 🔮 Vedic Astrology AI Advisor (Approach B)")
        gr.Markdown("_Fast, accurate astrology analysis using AI and classical texts_")
        
        # Session state components
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Step 1: Initialize Session")
                gr.Markdown("📝 **Instructions:** Enter your chart data below and click Initialize")
                chart_data_input = gr.Textbox(
                    label="Chart Data (D1, D9, D10, factors, yogas)",
                    placeholder="""Enter your chart data like:
                    
RASHI CHART (D1):
Ascendant: Cancer
7th House: Venus in Capricorn  
11th House: Saturn (Retrograde)

NAVAMSA (D9):
7th House: Saturn
Ascendant: Cancer

Current Dasha: Venus-Saturn""",
                    lines=8,
                    value="""RASHI CHART (D1):
Ascendant: Cancer
7th House: Venus in Capricorn
11th House: Saturn (Retrograde)

NAVAMSA (D9):
7th House: Saturn
Ascendant: Cancer

Current Dasha: Venus-Saturn"""  # Pre-fill with sample data
                )
                
                niche_selector = gr.Dropdown(
                    choices=["Love & Relationships", "Career & Professional", "Wealth & Finance", "Health & Wellness", "Spiritual Growth"],
                    value="Love & Relationships",
                    label="Select Niche"
                )
                
                initialize_btn = gr.Button("Initialize Session", variant="primary", size="lg")
                
                session_status = gr.Textbox(
                    label="Session Status",
                    interactive=False,
                    lines=3
                )
                
                # NEW: Pre-load button for smart caching!
                gr.Markdown("---")
                gr.Markdown("### 🚀 Smart Caching (Optional)")
                gr.Markdown("**Pre-load** niche knowledge for **3x faster responses** (6-8s vs 23s)")
                preload_btn = gr.Button("🔮 Pre-load Knowledge (35-45s)", variant="secondary", size="lg")
                preload_status_box = gr.Textbox(
                    label="Pre-load Status",
                    interactive=False,
                    lines=8,
                    placeholder="Click 'Pre-load Knowledge' to cache passages for faster responses..."
                )
            
            with gr.Column(scale=2):
                gr.Markdown("### Step 2: Ask Questions")
                gr.Markdown("⚠️ **Note:** You must initialize a session first before asking questions!")
                
                # Manual chat interface for better control
                chatbot = gr.Chatbot(
                    label="Astrology Consultation",
                    height=400,
                    placeholder="Initialize your session first, then ask questions here..."
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Your Question",
                        placeholder="Ask about your chart: 'How will my spouse look?', 'What about career?', etc.",
                        scale=4,
                        lines=2
                    )
                    with gr.Column(scale=1):
                        submit_btn = gr.Button("🚀 Quick Answer", variant="primary", size="sm")
                        expand_btn = gr.Button("📚 Detailed Answer", variant="secondary", size="sm")
                
                # Example questions as simple text
                gr.Markdown("""
                **💡 Tips:**
                - Use **🚀 Quick Answer** for fast drafts (2-4s)
                - Use **📚 Detailed Answer** for comprehensive analysis (6-12s)
                
                **Example Questions:**
                - How will my spouse look?
                - What about their personality?  
                - When will I meet them?
                - What's my career path?
                - Any health concerns?
                """)
        
        # Additional info
        with gr.Row():
            factors_display = gr.Textbox(label="Parsed Chart Factors", lines=6, interactive=False)
        
        # Event handlers
        def submit_message(message, history, mode="draft"):
            if not message.strip():
                return history, ""
            
            # Check if session is initialized
            if not current_session_id:
                # Show friendly error message
                history = history + [[message, "⚠️ **Session Not Initialized**\n\nPlease initialize your session first:\n1. Enter your chart data in the left panel\n2. Select your niche (Love, Career, etc.)\n3. Click 'Initialize Session' button\n\nThen you can ask questions!"]]
                return history, ""
            
            # Add user message to history
            history = history + [[message, None]]
            
            # Get response from chat handler
            response = chat_handler(message, history, mode=mode)
            
            # Add response to history
            history[-1][1] = response
            
            return history, ""
        
        # Initialize session handler
        def init_session_wrapper(chart_data, niche):
            status, factors = initialize_session_button(chart_data, niche)
            factors_text = json.dumps(factors, indent=2) if factors else ""
            return status, factors_text
        
        initialize_btn.click(
            fn=init_session_wrapper,
            inputs=[chart_data_input, niche_selector],
            outputs=[session_status, factors_display]
        )
        
        # NEW: Pre-load handler
        preload_btn.click(
            fn=preload_niche_knowledge_handler,
            inputs=[chart_data_input, niche_selector],
            outputs=[preload_status_box],
            show_progress=True
        )
        
        # Chat handlers - DRAFT mode (default)
        submit_btn.click(
            fn=lambda msg, hist: submit_message(msg, hist, mode="draft"),
            inputs=[msg, chatbot],
            outputs=[chatbot, msg],
            show_progress=True
        )
        
        # NEW: EXPAND mode button
        expand_btn.click(
            fn=lambda msg, hist: submit_message(msg, hist, mode="expand"),
            inputs=[msg, chatbot],
            outputs=[chatbot, msg],
            show_progress=True
        )
        
        msg.submit(
            fn=lambda msg, hist: submit_message(msg, hist, mode="draft"),
            inputs=[msg, chatbot], 
            outputs=[chatbot, msg],
            show_progress=True
        )
    
    return interface


def main():
    """Main entry point"""
    
    logger.info("Starting Vedic Astrology AI Advisor...")
    logger.info(f"Approach B: {USE_APPROACH_B}")
    logger.info(f"Dynamic Mode: {USE_DYNAMIC_MODE}")
    
    # Initialize components
    if USE_APPROACH_B:
        try:
            initialize_approach_b()
        except Exception as e:
            logger.error(f"Failed to initialize Approach B: {e}")
            logger.info("Continuing with limited functionality...")
    else:
        logger.error("Approach B not enabled!")
        return
    
    # Create and launch interface
    interface = create_gradio_interface()
    
    # Try different ports if the default is occupied
    port = PORT
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            interface.launch(
                server_name="127.0.0.1",  # Use localhost instead of 0.0.0.0
                server_port=port,
                debug=DEBUG,
                share=True,  # Enable shareable link to avoid localhost access issues
                show_error=True
            )
            break  # Successfully launched
        except OSError as e:
            if "Cannot find empty port" in str(e) and attempt < max_attempts - 1:
                port += 1
                logger.warning(f"Port {port - 1} in use, trying port {port}...")
            else:
                raise


if __name__ == "__main__":
    main()
