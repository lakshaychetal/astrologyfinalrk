"""
Cache-First RAG Retriever with Parallel Retrieval
Intelligently retrieves from cache before hitting RAG API
Professional implementation with fallback and tracking
Author: AI System Architect
"""

import time
import logging
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.cache_manager import get_cache_manager, build_cache_key
from niche_config import get_cache_ttl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CachedRetriever:
    """
    Cache-first RAG retrieval with intelligent fallback
    
    Features:
    - Cache-first strategy (90% hit rate expected)
    - Automatic cache updates for misses
    - Batch operations for efficiency
    - Hit/miss tracking
    - Graceful degradation
    """
    
    def __init__(
        self,
        rag_retriever,
        embeddings_client,
        cache_manager=None
    ):
        """
        Initialize cached retriever
        
        Args:
            rag_retriever: RAG retrieval agent
            embeddings_client: Embeddings generation agent  
            cache_manager: Cache manager (optional)
        """
        self.rag = rag_retriever
        self.embeddings = embeddings_client
        self.cache = cache_manager or get_cache_manager()
        
        self.retrieval_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "rag_calls": 0,
            "time_saved_ms": 0
        }
    
    def retrieve_with_cache(
        self,
        session_id: str,
        niche: str,
        required_factors: List[str],
        queries: Optional[List[str]] = None,
        embeddings: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Cache-first retrieval with intelligent fallback
        
        This is the main entry point for cached retrieval.
        
        Args:
            session_id: Session identifier
            niche: Astrology niche
            required_factors: List of factor names needed
            queries: Optional pre-generated queries
            embeddings: Optional pre-computed embeddings
        
        Returns:
            Dict with:
                - all_passages: Combined cached + fresh passages
                - cached_passages: Passages from cache
                - fresh_passages: Passages from RAG
                - cache_hit_rate: % of factors found in cache
                - time_saved_ms: Estimated time saved
                - retrieval_time_ms: Total retrieval time
        """
        start_time = time.time()
        
        logger.info(
            f"🔍 Cache-first retrieval for {len(required_factors)} factors "
            f"(session: {session_id[:8]}..., niche: {niche})"
        )
        
        cached_passages = []
        missing_factors = []
        
        # Step 1: Check cache for each required factor
        ttl_seconds = get_cache_ttl(niche)
        
        for factor in required_factors:
            cache_key = build_cache_key(session_id, niche, factor)
            
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                # Cache hit!
                cached_passages.extend(cached_data)
                self.retrieval_stats["cache_hits"] += 1
                logger.debug(f"  ✅ Cache hit: {factor}")
            else:
                # Cache miss - need to fetch
                missing_factors.append(factor)
                self.retrieval_stats["cache_misses"] += 1
                logger.debug(f"  ❌ Cache miss: {factor}")
        
        # Calculate cache hit rate
        cache_hit_rate = (
            len(required_factors) - len(missing_factors)
        ) / len(required_factors) if required_factors else 0
        
        logger.info(
            f"  Cache hit rate: {cache_hit_rate*100:.1f}% "
            f"({len(cached_passages)} passages from cache, "
            f"{len(missing_factors)} factors need RAG)"
        )
        
        # Step 2: Fetch missing factors from RAG in PARALLEL (if any)
        fresh_passages = []
        
        if missing_factors:
            logger.info(f"  🚀 Fetching {len(missing_factors)} missing factors from RAG (PARALLEL)...")
            
            try:
                # PHASE 2: PARALLEL RETRIEVAL for 3-5x speedup
                fresh_passages = self._parallel_rag_retrieval(
                    session_id=session_id,
                    niche=niche,
                    missing_factors=missing_factors,
                    ttl_seconds=ttl_seconds
                )
                
                self.retrieval_stats["rag_calls"] += 1
                
                logger.info(f"  ✅ Retrieved {len(fresh_passages)} fresh passages from RAG (parallel)")
                
            except Exception as e:
                logger.error(f"  ❌ RAG retrieval failed: {e}")
                # Continue with cached passages only
        
        # Step 3: Combine and return
        all_passages = cached_passages + fresh_passages
        
        # Estimate time saved by cache
        # Avg RAG retrieval: ~1.2s per query, cache: ~0.002s
        cache_hits = len(required_factors) - len(missing_factors)
        time_saved_ms = cache_hits * 1200  # 1.2s per cached factor
        self.retrieval_stats["time_saved_ms"] += time_saved_ms
        
        retrieval_time_ms = (time.time() - start_time) * 1000
        
        result = {
            "all_passages": all_passages,
            "cached_passages": cached_passages,
            "fresh_passages": fresh_passages,
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": cache_hits,
            "cache_misses": len(missing_factors),
            "time_saved_ms": time_saved_ms,
            "retrieval_time_ms": retrieval_time_ms,
        }
        
        logger.info(
            f"✅ Cached retrieval complete! "
            f"{len(all_passages)} total passages "
            f"(~{time_saved_ms/1000:.1f}s saved by cache) "
            f"in {retrieval_time_ms:.0f}ms"
        )
        
        return result
    
    def _generate_queries_for_factors(self, factors: List[str]) -> List[str]:
        """
        Generate RAG queries for missing factors
        
        Args:
            factors: List of factor names
        
        Returns:
            List of query strings (2-3 per factor)
        """
        queries = []
        
        for factor in factors:
            # Generate 2-3 queries per factor (keep it concise)
            factor_clean = factor.replace("_", " ")
            
            # TIMING/DASHA FACTORS
            if "dasha" in factor.lower() or "timing" in factor.lower():
                queries.append(f"{factor_clean} marriage timing prediction")
                queries.append(f"{factor_clean} spouse meeting period")
                queries.append(f"{factor_clean} relationship timing effects")
            
            elif "transit" in factor.lower():
                queries.append(f"{factor_clean} marriage timing effects")
                queries.append(f"{factor_clean} relationship activation")
            
            # VENUS FACTORS
            elif "venus" in factor.lower():
                queries.append(f"{factor_clean} spouse characteristics traits")
                queries.append(f"{factor_clean} marriage relationship")
            
            # 7TH HOUSE FACTORS
            elif "7th" in factor.lower():
                queries.append(f"{factor_clean} partnership marriage")
                queries.append(f"{factor_clean} spouse nature")
            
            # 10TH HOUSE FACTORS (Career)
            elif "10th" in factor.lower():
                queries.append(f"{factor_clean} career profession")
                queries.append(f"{factor_clean} work occupation")
            
            # GENERIC FACTORS
            else:
                queries.append(f"{factor_clean} significations meaning")
                if len(factor_clean.split()) <= 3:  # Short factors get extra query
                    queries.append(f"{factor_clean} astrological effects")
        
        return queries
    
    def _cache_fresh_passages(
        self,
        session_id: str,
        niche: str,
        missing_factors: List[str],
        fresh_passages: List[Dict],
        ttl_seconds: int
    ):
        """
        Cache freshly retrieved passages for future use
        
        Args:
            session_id: Session ID
            niche: Astrology niche
            missing_factors: Factors that were missing
            fresh_passages: Passages retrieved from RAG
            ttl_seconds: Cache TTL
        """
        # Group passages by factor (based on query)
        factor_passages = {factor: [] for factor in missing_factors}
        
        for passage in fresh_passages:
            query = passage.get("query", "")
            
            # Match passage to factor based on query content
            for factor in missing_factors:
                factor_keywords = factor.lower().replace("_", " ").split()
                query_lower = query.lower()
                
                # If query contains factor keywords, it belongs to that factor
                if any(kw in query_lower for kw in factor_keywords):
                    factor_passages[factor].append(passage)
                    break
        
        # Cache each factor's passages
        for factor, passages in factor_passages.items():
            if passages:
                cache_key = build_cache_key(session_id, niche, factor)
                self.cache.set(cache_key, passages, ttl_seconds)
                logger.debug(f"  💾 Cached {len(passages)} passages for {factor}")
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Get retrieval statistics
        
        Returns:
            Dict with cache hits, misses, time saved, etc.
        """
        total_requests = (
            self.retrieval_stats["cache_hits"] + 
            self.retrieval_stats["cache_misses"]
        )
        
        hit_rate = (
            self.retrieval_stats["cache_hits"] / total_requests
            if total_requests > 0
            else 0.0
        )
        
        return {
            **self.retrieval_stats,
            "total_factor_requests": total_requests,
            "hit_rate": hit_rate,
            "time_saved_seconds": self.retrieval_stats["time_saved_ms"] / 1000,
        }
    
    def clear_stats(self):
        """Reset retrieval statistics"""
        self.retrieval_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "rag_calls": 0,
            "time_saved_ms": 0
        }
    
    def _parallel_rag_retrieval(
        self,
        session_id: str,
        niche: str,
        missing_factors: List[str],
        ttl_seconds: int,
        max_workers: int = 8
    ) -> List[Dict[str, Any]]:
        """
        PHASE 2: Parallel RAG retrieval for 3-5x speedup
        
        Fetches multiple factors simultaneously using ThreadPoolExecutor
        instead of sequential retrieval. Critical for handling 120+ factors.
        
        Args:
            session_id: Session identifier
            niche: Astrology niche
            missing_factors: Factors not found in cache
            ttl_seconds: Cache TTL
            max_workers: Maximum parallel threads (default: 8)
        
        Returns:
            List of passages retrieved from RAG
        """
        all_passages = []
        
        # Create thread pool for parallel retrieval
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit retrieval tasks for each factor
            future_to_factor = {
                executor.submit(
                    self._retrieve_single_factor,
                    factor
                ): factor
                for factor in missing_factors
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_factor):
                factor = future_to_factor[future]
                
                try:
                    passages = future.result()
                    
                    if passages:
                        all_passages.extend(passages)
                        
                        # Cache this factor's passages
                        cache_key = build_cache_key(session_id, niche, factor)
                        self.cache.set(cache_key, passages, ttl_seconds)
                        
                        logger.debug(f"  ✅ Parallel retrieved & cached: {factor} ({len(passages)} passages)")
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to retrieve {factor}: {e}")
        
        return all_passages
    
    def _retrieve_single_factor(self, factor: str) -> List[Dict[str, Any]]:
        """
        Retrieve a single factor from RAG
        
        Thread-safe method for parallel execution
        
        Args:
            factor: Factor name (e.g., "venus_7th_house")
        
        Returns:
            List of passages for this factor
        """
        try:
            # Generate query for this factor
            query = self._generate_query_for_factor(factor)
            
            # Embed query
            embedding = self.embeddings.embed_queries([query])[0]
            
            # Retrieve from RAG
            rag_results = self.rag.retrieve_passages(
                queries=[query],
                embeddings=[embedding]
            )
            
            # Handle different RAG retriever formats
            if isinstance(rag_results, list):
                # Direct list of passages (REAL RAG format)
                return rag_results
            elif isinstance(rag_results, dict) and "passages" in rag_results:
                # Dict with passages key
                return rag_results["passages"]
            else:
                # Assume it's a list of result dicts (MOCK format)
                passages = []
                for result in rag_results:
                    if isinstance(result, dict) and "passages" in result:
                        passages.extend(result["passages"])
                return passages
        
        except Exception as e:
            logger.error(f"  ❌ Error retrieving {factor}: {e}")
            return []
    
    def _generate_query_for_factor(self, factor: str) -> str:
        """
        Generate a RAG query for a single factor
        
        Args:
            factor: Factor name (e.g., "venus_combustion")
        
        Returns:
            Query string optimized for RAG retrieval
        """
        # Convert factor name to natural language query
        # Example: "venus_combustion" → "venus combustion effects"
        
        factor_clean = factor.replace("_", " ")
        
        # Add context keywords for better retrieval
        if "dasha" in factor or "timing" in factor:
            return f"{factor_clean} period timing predictions"
        elif "house" in factor:
            return f"{factor_clean} placement significance"
        elif "yoga" in factor:
            return f"{factor_clean} combination effects"
        elif "transit" in factor:
            return f"{factor_clean} current influence"
        else:
            return f"{factor_clean} vedic astrology interpretation"
    
    def retrieve_multi_stage(
        self,
        session_id: str,
        niche: str,
        question: str,
        broad_factors: List[str],
        deep_factors: List[str],
        queries: Optional[List[str]] = None,
        embeddings: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        PHASE 4: Multi-stage retrieval for breadth + depth
        
        Two-stage approach:
        1. BROAD STAGE: Retrieve from 15-20 factors (60-80 passages)
        2. DEEP STAGE: Deep-dive into top 5 factors with question context (30-40 more passages)
        
        This ensures comprehensive coverage (breadth) while maintaining
        expert-level depth on the most critical factors.
        
        Args:
            session_id: Session identifier
            niche: Astrology niche
            question: User's original question (for context)
            broad_factors: 15-20 factors for broad coverage
            deep_factors: Top 5 factors for deep analysis
            queries: Optional pre-generated queries
            embeddings: Optional pre-computed embeddings
        
        Returns:
            Dict with:
                - all_passages: Combined broad + deep passages (90-120 total)
                - broad_passages: Stage 1 passages (60-80)
                - deep_passages: Stage 2 passages (30-40)
                - total_factors_used: Total unique factors
                - retrieval_time_ms: Total time
        """
        start_time = time.time()
        
        logger.info(
            f"🎯 Multi-stage retrieval: "
            f"{len(broad_factors)} broad + {len(deep_factors)} deep factors"
        )
        
        # STAGE 1: Broad retrieval (cache-first)
        logger.info("  📊 Stage 1: Broad coverage retrieval...")
        broad_result = self.retrieve_with_cache(
            session_id=session_id,
            niche=niche,
            required_factors=broad_factors,
            queries=queries,
            embeddings=embeddings
        )
        
        broad_passages = broad_result["all_passages"]
        logger.info(f"  ✅ Stage 1 complete: {len(broad_passages)} passages from {len(broad_factors)} factors")
        
        # STAGE 2: Deep-dive retrieval with question context
        logger.info("  🔍 Stage 2: Deep-dive retrieval...")
        deep_passages = self._deep_dive_retrieval(
            session_id=session_id,
            niche=niche,
            question=question,
            deep_factors=deep_factors
        )
        
        logger.info(f"  ✅ Stage 2 complete: {len(deep_passages)} deep passages from {len(deep_factors)} factors")
        
        # Combine results
        all_passages = broad_passages + deep_passages
        total_time_ms = (time.time() - start_time) * 1000
        
        # Deduplicate passages (same content from different stages)
        unique_passages = self._deduplicate_passages(all_passages)
        
        logger.info(
            f"✅ Multi-stage retrieval complete: "
            f"{len(unique_passages)} unique passages "
            f"(from {len(broad_factors)} broad + {len(deep_factors)} deep factors) "
            f"in {total_time_ms:.0f}ms"
        )
        
        return {
            "all_passages": unique_passages,
            "broad_passages": broad_passages,
            "deep_passages": deep_passages,
            "broad_factor_count": len(broad_factors),
            "deep_factor_count": len(deep_factors),
            "total_factors_used": len(set(broad_factors + deep_factors)),
            "total_passages": len(unique_passages),
            "retrieval_time_ms": total_time_ms,
            "cache_hit_rate": broad_result.get("cache_hit_rate", 0),
        }
    
    def _deep_dive_retrieval(
        self,
        session_id: str,
        niche: str,
        question: str,
        deep_factors: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Stage 2: Deep-dive retrieval with question context
        
        For the most critical factors, we generate question-specific queries
        to retrieve highly targeted passages.
        
        Args:
            session_id: Session identifier
            niche: Astrology niche
            question: User's original question
            deep_factors: Top 5 most important factors
        
        Returns:
            List of deep-dive passages
        """
        deep_passages = []
        
        for factor in deep_factors:
            # Generate question-specific query for this factor
            deep_query = self._generate_deep_query(factor, question)
            
            try:
                # Embed the deep query
                deep_embedding = self.embeddings.embed_queries([deep_query])[0]
                
                # Retrieve with question context
                rag_results = self.rag.retrieve_passages(
                    queries=[deep_query],
                    embeddings=[deep_embedding]
                )
                
                # Handle different RAG retriever formats
                if isinstance(rag_results, list):
                    passages = rag_results
                elif isinstance(rag_results, dict) and "passages" in rag_results:
                    passages = rag_results["passages"]
                else:
                    passages = []
                    for result in rag_results:
                        if isinstance(result, dict) and "passages" in result:
                            passages.extend(result["passages"])
                
                deep_passages.extend(passages)
                logger.debug(f"    🔍 Deep-dive: {factor} → {len(passages)} passages")
                
            except Exception as e:
                logger.error(f"    ❌ Deep-dive failed for {factor}: {e}")
        
        return deep_passages
    
    def _generate_deep_query(self, factor: str, question: str) -> str:
        """
        Generate question-specific deep-dive query
        
        Combines the factor with the user's question for highly targeted retrieval
        
        Args:
            factor: Factor name (e.g., "venus_7th_house")
            question: User's question (e.g., "How will my spouse look?")
        
        Returns:
            Deep query string
        """
        factor_clean = factor.replace("_", " ")
        
        # Extract key intent from question
        question_lower = question.lower()
        
        if "when" in question_lower:
            return f"{factor_clean} timing predictions for {question}"
        elif "how" in question_lower and ("look" in question_lower or "appear" in question_lower):
            return f"{factor_clean} physical appearance traits characteristics {question}"
        elif "how" in question_lower:
            return f"{factor_clean} detailed analysis {question}"
        elif "where" in question_lower:
            return f"{factor_clean} location meeting place {question}"
        elif "what" in question_lower:
            return f"{factor_clean} specific details {question}"
        elif "why" in question_lower:
            return f"{factor_clean} reasons causes explanation {question}"
        else:
            return f"{factor_clean} comprehensive analysis {question}"
    
    def _deduplicate_passages(
        self,
        passages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate passages based on content
        
        Args:
            passages: List of passage dicts
        
        Returns:
            Deduplicated list
        """
        seen_content = set()
        unique_passages = []
        
        for passage in passages:
            # Extract content (handle different formats)
            content = passage.get("content") or passage.get("text") or str(passage)
            
            # Use first 200 chars as fingerprint
            fingerprint = content[:200].strip().lower()
            
            if fingerprint not in seen_content:
                seen_content.add(fingerprint)
                unique_passages.append(passage)
        
        return unique_passages
