"""
AstroAirk Agents Module

Optimized components for fast Vedic astrology analysis:
- OpenRouter Synthesizer (GPT-4.1 Mini - primary)
- Modern Synthesizer (Gemini - fallback)
- Smart Orchestrator (main coordination)
- RAG Retrievers (Vertex AI + caching)
- Fast Reranker (NumPy-based)
- Semantic Selector (chart highlights)
- Niche Preloader (knowledge caching)
"""

from .openrouter_synthesizer import OpenRouterSynthesizer
from .modern_synthesizer import ModernSynthesizer
from .smart_orchestrator import SmartOrchestrator
from .simple_chart_parser import ChartParser
from .gemini_embeddings import GeminiEmbeddings
from .question_complexity import QuestionComplexityClassifier
from .validator import LightweightValidator
from .real_rag_retriever import RealRAGRetriever
from .vector_search_retriever import VectorSearchRetriever
from .cached_retriever import CachedRetriever
from .semantic_selector import SemanticFactorSelector
from .niche_preloader import NichePreloader
from .fast_reranker import FastReranker

__all__ = [
    'OpenRouterSynthesizer',
    'ModernSynthesizer',
    'SmartOrchestrator',
    'ChartParser',
    'GeminiEmbeddings',
    'QuestionComplexityClassifier',
    'LightweightValidator',
    'RealRAGRetriever',
    'VectorSearchRetriever',
    'CachedRetriever',
    'SemanticFactorSelector',
    'NichePreloader',
    'FastReranker',
]
