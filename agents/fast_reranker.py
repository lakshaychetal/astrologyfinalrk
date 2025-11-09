"""
Fast NumPy-based passage reranker
Replaces slow LLM reranking with vectorized operations
Target: 5-20ms for reranking
Author: Performance Optimization Team
"""

import numpy as np
import logging
import time
import re
from typing import List, Dict, Set, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FastReranker:
    """
    Vectorized NumPy reranker for passage scoring
    
    Features:
    - Cosine distance scoring
    - IDF-weighted token overlap
    - Tag matching bonuses
    - Length penalties
    - Sub-20ms execution time
    
    Replaces: LLM-based reranking (slow, expensive)
    """
    
    def __init__(
        self,
        distance_weight: float = 1.0,
        idf_weight: float = 0.35,
        tag_weight: float = 0.2,
        length_penalty_weight: float = 0.15,
        proximity_bonus: float = 0.2,
    ):
        """
        Initialize fast reranker
        
        Args:
            distance_weight: Weight for cosine similarity (default: 1.0)
            idf_weight: Weight for IDF token overlap (default: 0.35)
            tag_weight: Weight for tag matching (default: 0.2)
            length_penalty_weight: Weight for length penalty (default: 0.15)
            proximity_bonus: Bonus for very close matches (default: 0.2)
        """
        self.distance_weight = distance_weight
        self.idf_weight = idf_weight
        self.tag_weight = tag_weight
        self.length_penalty_weight = length_penalty_weight
        self.proximity_bonus = proximity_bonus
        
        # IDF cache for common terms
        self._idf_cache: Dict[str, float] = {}
    
    def rerank(
        self,
        passages: List[Dict[str, Any]],
        query: str,
        query_tokens: Optional[Set[str]] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank passages using vectorized NumPy operations
        
        Args:
            passages: List of passage dicts with 'text'/'passage' and 'relevance_score'/'distance'
            query: Original query string
            query_tokens: Pre-tokenized query (optional, for speed)
            top_k: Return only top K passages (optional)
        
        Returns:
            List of reranked passages (sorted by score, descending)
        """
        start_time = time.time()
        
        if not passages:
            return []
        
        if len(passages) == 1:
            return passages
        
        # Extract passage texts
        texts = [
            p.get("text") or p.get("passage") or p.get("content") or ""
            for p in passages
        ]
        
        # Tokenize query if not provided
        if query_tokens is None:
            query_tokens = self._tokenize(query)
        
        # Tokenize all passages (vectorized)
        passage_token_sets = [self._tokenize(text) for text in texts]
        
        # Extract existing distances/scores (vectorized)
        distances = np.array([
            self._extract_distance(p)
            for p in passages
        ])
        
        # Calculate IDF overlap scores (vectorized)
        idf_scores = np.array([
            self._calculate_idf_overlap(query_tokens, p_tokens)
            for p_tokens in passage_token_sets
        ])
        
        # Calculate length penalties (vectorized)
        lengths = np.array([len(text) for text in texts])
        length_scores = self._calculate_length_penalties(lengths)
        
        # Calculate tag match bonuses (vectorized)
        tag_scores = np.array([
            self._calculate_tag_match(query, p.get("tags", []) or [])
            for p in passages
        ])
        
        # Proximity bonuses for very close matches
        proximity_bonuses = (distances < 0.3).astype(float) * self.proximity_bonus
        
        # Combine all scores (vectorized)
        final_scores = (
            self.distance_weight * (1.0 - distances) +
            self.idf_weight * idf_scores +
            self.tag_weight * tag_scores +
            self.length_penalty_weight * length_scores +
            proximity_bonuses
        )
        
        # Sort by score (descending)
        sorted_indices = np.argsort(-final_scores)
        
        # Apply top_k filter
        if top_k:
            sorted_indices = sorted_indices[:top_k]
        
        # Build reranked list
        reranked = []
        for idx in sorted_indices:
            passage = passages[int(idx)]
            passage["rerank_score"] = float(final_scores[idx])
            passage["original_rank"] = int(idx)
            reranked.append(passage)
        
        rerank_time_ms = (time.time() - start_time) * 1000
        
        logger.debug(
            f"  ⚡ Fast rerank: {len(passages)} passages in {rerank_time_ms:.1f}ms "
            f"(top_k={top_k or 'all'})"
        )
        
        return reranked
    
    def _extract_distance(self, passage: Dict[str, Any]) -> float:
        """
        Extract distance/score from passage
        
        Args:
            passage: Passage dict
        
        Returns:
            Distance value (0.0-1.0, lower = more similar)
        """
        # Try different field names
        if "distance" in passage:
            return float(passage["distance"])
        elif "relevance_score" in passage:
            # Convert similarity to distance
            return 1.0 - float(passage["relevance_score"])
        elif "relevance" in passage:
            return 1.0 - float(passage["relevance"])
        elif "similarity_score" in passage:
            return 1.0 - float(passage["similarity_score"])
        else:
            # Default: assume medium similarity
            return 0.5
    
    def _tokenize(self, text: str) -> Set[str]:
        """
        Fast tokenization for overlap calculation
        
        Args:
            text: Input text
        
        Returns:
            Set of lowercase tokens (length > 2)
        """
        if not text:
            return set()
        
        # Extract alphanumeric tokens
        tokens = re.findall(r'[a-z0-9]+', text.lower())
        
        # Filter out short tokens and stopwords
        stopwords = {'the', 'and', 'or', 'is', 'in', 'at', 'to', 'of', 'for', 'a', 'an'}
        
        return {
            token for token in tokens
            if len(token) > 2 and token not in stopwords
        }
    
    def _calculate_idf_overlap(
        self,
        query_tokens: Set[str],
        passage_tokens: Set[str]
    ) -> float:
        """
        Calculate IDF-weighted token overlap
        
        Args:
            query_tokens: Query token set
            passage_tokens: Passage token set
        
        Returns:
            IDF overlap score (0.0-1.0)
        """
        if not query_tokens or not passage_tokens:
            return 0.0
        
        # Find overlapping tokens
        overlap = query_tokens & passage_tokens
        
        if not overlap:
            return 0.0
        
        # Simple IDF approximation (longer words = higher weight)
        # In production, use precomputed IDF from corpus
        idf_sum = sum(len(token) / 10.0 for token in overlap)
        
        # Normalize by query length
        max_idf = sum(len(token) / 10.0 for token in query_tokens)
        
        if max_idf == 0:
            return 0.0
        
        return min(1.0, idf_sum / max_idf)
    
    def _calculate_length_penalties(self, lengths: np.ndarray) -> np.ndarray:
        """
        Calculate length penalty scores (vectorized)
        
        Penalize very short (<100) and very long (>1500) passages
        
        Args:
            lengths: Array of passage lengths
        
        Returns:
            Array of length scores (0.0-1.0)
        """
        # Optimal range: 300-900 characters
        optimal_min = 300
        optimal_max = 900
        
        # Normalize to optimal range
        normalized = np.clip(lengths, optimal_min, optimal_max)
        
        # Score: 1.0 at optimal, lower outside
        scores = 1.0 - np.abs(normalized - (optimal_min + optimal_max) / 2) / optimal_max
        
        return np.clip(scores, 0.0, 1.0)
    
    def _calculate_tag_match(
        self,
        query: str,
        tags: List[str]
    ) -> float:
        """
        Calculate tag matching bonus
        
        Args:
            query: Query string
            tags: List of passage tags
        
        Returns:
            Tag match score (0.0-1.0)
        """
        if not tags:
            return 0.0
        
        query_lower = query.lower()
        
        # Count matching tags
        matches = sum(
            1 for tag in tags
            if tag.lower() in query_lower
        )
        
        # Normalize by total tags
        return min(1.0, matches / len(tags))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reranker statistics"""
        return {
            "idf_cache_size": len(self._idf_cache),
            "weights": {
                "distance": self.distance_weight,
                "idf": self.idf_weight,
                "tag": self.tag_weight,
                "length_penalty": self.length_penalty_weight,
                "proximity_bonus": self.proximity_bonus,
            }
        }


# Convenience function for quick reranking
def rerank_passages(
    passages: List[Dict[str, Any]],
    query: str,
    top_k: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function for fast reranking
    
    Args:
        passages: List of passage dicts
        query: Query string
        top_k: Return only top K
    
    Returns:
        Reranked passages
    """
    reranker = FastReranker()
    return reranker.rerank(passages, query, top_k=top_k)
