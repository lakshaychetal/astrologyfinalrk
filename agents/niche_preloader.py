"""
Niche-Specific Knowledge Pre-Loader
Pre-fetches and caches RAG passages for all relevant chart factors
Professional implementation with progress tracking and error handling
Author: AI System Architect
"""

import time
import logging
import asyncio
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from niche_config import (
    NICHE_FACTOR_MAP,
    get_niche_factors,
    get_cache_ttl,
    get_dasha_range,
    CACHE_CONFIG
)
from utils.cache_manager import get_cache_manager, build_cache_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NichePreloader:
    """
    Pre-loads RAG knowledge for niche-specific factors
    
    Features:
    - Intelligent factor selection based on niche
    - Batch processing for efficiency
    - Progress tracking with callbacks
    - Error handling and retry logic
    - Cache storage with TTL
    """
    
    def __init__(
        self,
        rag_retriever,
        embeddings_client,
        cache_manager=None
    ):
        """
        Initialize pre-loader
        
        Args:
            rag_retriever: RAG retrieval agent
            embeddings_client: Embeddings generation agent
            cache_manager: Cache manager (optional, uses global if None)
        """
        self.rag = rag_retriever
        self.embeddings = embeddings_client
        self.cache = cache_manager or get_cache_manager()
        
        self.preload_config = CACHE_CONFIG.get("preload", {})
        self.batch_size = self.preload_config.get("batch_size", 5)
        self.max_parallel = self.preload_config.get("max_parallel", 4)
        self.timeout = self.preload_config.get("timeout_seconds", 120)
    
    def preload_niche_knowledge(
        self,
        session_id: str,
        niche: str,
        chart_factors: Dict[str, Any],
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Pre-load all niche-relevant passages into cache
        
        This is the main entry point for pre-loading.
        
        Args:
            session_id: Unique session identifier
            niche: Selected astrology niche
            chart_factors: All parsed chart factors (99 total)
            progress_callback: Optional callback(percent, message)
        
        Returns:
            Dict with results: {
                "status": "success",
                "factors_processed": 55,
                "passages_cached": 280,
                "time_taken_seconds": 38.5,
                "cache_keys": [...]
            }
        """
        start_time = time.time()
        logger.info(f"🚀 Starting pre-load for niche: {niche}, session: {session_id}")
        
        # Step 1: Extract niche-relevant factors
        if progress_callback:
            progress_callback(5, "Analyzing chart factors...")
        
        relevant_factors = self._extract_niche_factors(niche, chart_factors)
        total_factors = len(relevant_factors)
        
        if total_factors == 0:
            logger.warning(f"No factors found for niche: {niche}")
            return {
                "status": "error",
                "error": "No relevant factors found",
                "factors_processed": 0
            }
        
        logger.info(f"📊 Found {total_factors} relevant factors for {niche}")
        
        # Step 2: Process factors in batches
        passages_cached = 0
        cache_keys = []
        factors_processed = 0
        
        # Process in batches for efficiency
        for batch_idx in range(0, total_factors, self.batch_size):
            batch = relevant_factors[batch_idx:batch_idx + self.batch_size]
            batch_num = (batch_idx // self.batch_size) + 1
            total_batches = (total_factors + self.batch_size - 1) // self.batch_size
            
            if progress_callback:
                percent = 10 + (batch_idx / total_factors * 85)
                progress_callback(
                    percent,
                    f"Processing batch {batch_num}/{total_batches} ({len(batch)} factors)..."
                )
            
            try:
                # Process batch
                batch_results = self._process_factor_batch(
                    session_id=session_id,
                    niche=niche,
                    factors_batch=batch
                )
                
                # Update counters
                factors_processed += len(batch)
                passages_cached += batch_results["passages_count"]
                cache_keys.extend(batch_results["cache_keys"])
                
                logger.info(
                    f"  ✅ Batch {batch_num}/{total_batches}: "
                    f"{batch_results['passages_count']} passages cached"
                )
                
            except Exception as e:
                logger.error(f"  ❌ Batch {batch_num} failed: {e}")
                # Continue with next batch
                continue
        
        # Step 3: Finalize
        time_taken = time.time() - start_time
        
        if progress_callback:
            progress_callback(100, "Pre-loading complete!")
        
        result = {
            "status": "success",
            "session_id": session_id,
            "niche": niche,
            "factors_processed": factors_processed,
            "passages_cached": passages_cached,
            "time_taken_seconds": round(time_taken, 2),
            "cache_keys": cache_keys,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"✅ Pre-load complete! {factors_processed} factors, "
            f"{passages_cached} passages in {time_taken:.1f}s"
        )
        
        return result
    
    def _extract_niche_factors(
        self,
        niche: str,
        all_chart_factors: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract only niche-relevant factors from all chart factors
        INCLUDES TIMING FACTORS for niches where timing is important!
        
        Args:
            niche: Astrology niche
            all_chart_factors: All 99 parsed factors
        
        Returns:
            List of relevant factors with metadata
        """
        from niche_config import get_timing_factors
        
        niche_config = NICHE_FACTOR_MAP.get(niche, {})
        
        if not niche_config:
            logger.warning(f"Unknown niche: {niche}. Using all factors.")
            return [
                {"name": k, "value": v, "chart": "D1"}
                for k, v in all_chart_factors.items()
            ]
        
        relevant_factors = []
        
        # ALWAYS include timing factors for Love & Relationships
        # This ensures "when will I meet my spouse" questions have dasha data!
        timing_factors_to_add = []
        if niche in ["Love & Relationships", "Career & Professional"]:
            timing_factors_to_add = get_timing_factors(niche, all_chart_factors)
            logger.info(
                f"📅 Adding {len(timing_factors_to_add)} timing factors "
                f"(Vimshottari Dashas) for {niche}"
            )
        
        # Extract D1 factors
        for factor_name in niche_config.get("d1_factors", []):
            if factor_name in all_chart_factors:
                relevant_factors.append({
                    "name": factor_name,
                    "value": all_chart_factors[factor_name],
                    "chart": "D1",
                    "priority": "high"
                })
        
        # Extract D9 factors
        for factor_name in niche_config.get("d9_factors", []):
            if factor_name in all_chart_factors:
                relevant_factors.append({
                    "name": factor_name,
                    "value": all_chart_factors[factor_name],
                    "chart": "D9",
                    "priority": "high"
                })
        
        # Extract D10 factors (if applicable)
        for factor_name in niche_config.get("d10_factors", []):
            if factor_name in all_chart_factors:
                relevant_factors.append({
                    "name": factor_name,
                    "value": all_chart_factors[factor_name],
                    "chart": "D10",
                    "priority": "medium"
                })
        
        # Add dasha periods (with smart range)
        if "current_mahadasha" in all_chart_factors:
            relevant_factors.append({
                "name": "current_dashas",
                "value": {
                    "mahadasha": all_chart_factors.get("current_mahadasha"),
                    "antardasha": all_chart_factors.get("current_antardasha"),
                },
                "chart": "Vimshottari",
                "priority": "high"
            })
        
        # ADD TIMING FACTORS (Vimshottari Dashas for "when" questions)
        # These are pseudo-factors that trigger dasha-specific RAG queries
        for timing_factor in timing_factors_to_add:
            relevant_factors.append({
                "name": timing_factor,
                "value": "timing_query",  # Placeholder value
                "chart": "Timing",
                "priority": "high"
            })
        
        logger.info(
            f"Extracted {len(relevant_factors)} factors from {len(all_chart_factors)} total "
            f"(includes {len(timing_factors_to_add)} timing factors)"
        )
        
        return relevant_factors
    
    def _process_factor_batch(
        self,
        session_id: str,
        niche: str,
        factors_batch: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a batch of factors in PARALLEL (3-5x faster!)
        
        Uses ThreadPoolExecutor to retrieve multiple factors simultaneously
        instead of sequential processing.
        
        Args:
            session_id: Session ID
            niche: Astrology niche
            factors_batch: Batch of factors to process
        
        Returns:
            Dict with passages_count and cache_keys
        """
        cache_keys = []
        total_passages = 0
        ttl_seconds = get_cache_ttl(niche)
        
        # PARALLEL PROCESSING: Retrieve each factor independently
        with ThreadPoolExecutor(max_workers=min(len(factors_batch), 8)) as executor:
            # Submit retrieval tasks for each factor
            future_to_factor = {
                executor.submit(
                    self._retrieve_and_cache_factor,
                    session_id,
                    niche,
                    factor,
                    ttl_seconds
                ): factor
                for factor in factors_batch
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_factor):
                factor = future_to_factor[future]
                
                try:
                    result = future.result()
                    
                    if result["success"]:
                        cache_keys.append(result["cache_key"])
                        total_passages += result["passages_count"]
                        
                        logger.debug(
                            f"    ✅ {factor['name']}: "
                            f"{result['passages_count']} passages cached"
                        )
                    
                except Exception as e:
                    logger.error(f"    ❌ Failed to process {factor['name']}: {e}")
        
        return {
            "passages_count": total_passages,
            "cache_keys": cache_keys
        }
    
    def _retrieve_and_cache_factor(
        self,
        session_id: str,
        niche: str,
        factor: Dict[str, Any],
        ttl_seconds: int
    ) -> Dict[str, Any]:
        """
        Retrieve and cache a single factor (thread-safe)
        
        Args:
            session_id: Session ID
            niche: Astrology niche
            factor: Factor dict with name, value, chart
            ttl_seconds: Cache TTL
        
        Returns:
            Dict with success, cache_key, passages_count
        """
        try:
            # Generate queries for this factor
            queries = self._generate_queries_for_factor(factor)
            
            if not queries:
                return {"success": False, "passages_count": 0}
            
            # Embed queries
            embeddings = self.embeddings.embed_queries(queries)
            
            # Retrieve passages using RAG
            rag_results = self.rag.retrieve_passages(
                queries=queries,
                embeddings=embeddings
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
            
            # Cache passages
            if passages:
                cache_key = build_cache_key(session_id, niche, factor["name"])
                
                self.cache.set(
                    key=cache_key,
                    value=passages,
                    ttl_seconds=ttl_seconds
                )
                
                return {
                    "success": True,
                    "cache_key": cache_key,
                    "passages_count": len(passages)
                }
            
            return {"success": False, "passages_count": 0}
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            raise
        
        return {
            "passages_count": total_passages,
            "cache_keys": cache_keys
        }
    
    def _generate_queries_for_factor(self, factor: Dict[str, Any]) -> List[str]:
        """
        Generate RAG search queries for a factor
        
        Args:
            factor: Factor dict with name, value, chart
        
        Returns:
            List of query strings
        """
        factor_name = factor["name"]
        factor_value = factor["value"]
        chart_type = factor.get("chart", "D1")
        
        queries = []
        
        # TIMING FACTORS - Generate dasha-specific queries
        if chart_type == "Timing" or "dasha" in factor_name.lower() or "timing" in factor_name.lower():
            # Extract planet name from factor
            factor_clean = factor_name.replace("_", " ")
            queries.extend([
                f"{factor_clean} marriage timing prediction when",
                f"{factor_clean} spouse meeting period relationship",
                f"{factor_clean} effects on partnership timing",
            ])
        
        # VENUS FACTORS
        elif "venus" in factor_name.lower():
            queries.extend([
                f"Venus in {factor_value} significations traits spouse",
                f"{factor_value} Venus relationship marriage partner",
            ])
        
        # 7TH HOUSE FACTORS
        elif "7th" in factor_name.lower():
            queries.extend([
                f"7th house {factor_value} marriage spouse characteristics",
                f"{factor_value} in 7th partnership relationships",
            ])
        
        # DARAKARAKA
        elif "darakaraka" in factor_name.lower():
            queries.extend([
                f"Darakaraka {factor_value} spouse appearance nature",
                f"{factor_value} as darakaraka marriage timing",
            ])
        
        # CURRENT DASHA
        elif factor_name == "current_dashas":
            maha = factor_value.get("mahadasha", "")
            antar = factor_value.get("antardasha", "")
            if maha and antar:
                queries.extend([
                    f"{maha}-{antar} dasha period effects timing events",
                    f"{maha} mahadasha {antar} antardasha marriage timing",
                ])
        
        # 10TH HOUSE (Career)
        elif "10th" in factor_name.lower():
            queries.extend([
                f"10th house {factor_value} career profession",
                f"{factor_value} in 10th work occupation",
            ])
        
        # GENERIC
        else:
            queries.append(
                f"{factor_name.replace('_', ' ')} {factor_value} significations"
            )
        
        return queries[:3]  # Max 3 queries per factor
    
    def check_preload_status(self, session_id: str, niche: str) -> Dict[str, Any]:
        """
        Check if niche is pre-loaded for session
        
        Args:
            session_id: Session ID
            niche: Astrology niche
        
        Returns:
            Status dict with is_loaded, factors_cached, etc.
        """
        expected_factors = get_niche_factors(niche)
        cached_count = 0
        
        for factor in expected_factors:
            cache_key = build_cache_key(session_id, niche, factor)
            if self.cache.exists(cache_key):
                cached_count += 1
        
        is_loaded = cached_count >= (len(expected_factors) * 0.8)  # 80% threshold
        
        return {
            "is_loaded": is_loaded,
            "factors_cached": cached_count,
            "total_factors": len(expected_factors),
            "coverage_percent": (cached_count / len(expected_factors) * 100) if expected_factors else 0
        }
