"""
FAST RAG Retriever using Vertex AI RAG API
Purpose: Retrieve classical astrology passages from your RAG corpus
Uses: vertexai.preview.rag.retrieval_query() - FAST method (200-500ms per query)
Replaces: Slow generate_content with RAG tools (7-11s per query)

OPTIMIZATIONS:
- Merged queries: 1 Vertex call instead of 4 (2400ms → 600-900ms)
- Fast NumPy reranker: 5-20ms instead of LLM rerank
- Top-K=6 retrieval → rerank to top-3 for LLM
"""

import time
import logging
from typing import List, Dict, Optional

from vertexai.preview import rag
import vertexai

# Import fast reranker
from agents.fast_reranker import FastReranker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealRAGRetriever:
    """
    FAST RAG retriever using Vertex AI RAG API
    Uses retrieval_query() for direct corpus search (10-20x faster than generation)
    """
    
    def __init__(
        self,
        project_id: str,
        location: str,
        corpus_id: str,
        top_k: int = 6,  # Retrieve top 6, rerank to top 3
        similarity_threshold: float = 0.5,
        final_top_k: int = 3  # Final passages after reranking
    ):
        """
        Initialize FAST RAG retriever with reranking
        
        Args:
            project_id (str): Google Cloud project ID
            location (str): Region (e.g., "asia-south1")
            corpus_id (str): RAG corpus ID (from your .env)
            top_k (int): Number of passages to retrieve per query (default: 6)
            similarity_threshold (float): Minimum similarity score (0.0-1.0)
            final_top_k (int): Final passages after reranking (default: 3)
        """
        self.project_id = project_id
        self.location = location
        self.corpus_id = corpus_id
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.final_top_k = final_top_k
        self.rag_corpus = None
        
        # Initialize fast reranker
        self.reranker = FastReranker()
        
        self._initialize_corpus()
    
    def _initialize_corpus(self):
        """Initialize Vertex AI RAG Corpus"""
        try:
            # Initialize Vertex AI
            vertexai.init(
                project=self.project_id,
                location=self.location
            )
            
            # Store corpus resource name for retrieval_query
            self.corpus_resource_name = (
                f"projects/{self.project_id}/locations/{self.location}/"
                f"ragCorpora/{self.corpus_id}"
            )
            
            logger.info(
                f"✅ FAST RAG initialized! "
                f"Corpus: {self.corpus_id}, Top-K: {self.top_k}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG: {str(e)}")
            raise
    
    def retrieve_passages(
        self,
        queries: List[str],
        embeddings: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        OPTIMIZED retrieval using SINGLE merged query (1 Vertex call)
        Merges multiple enriched queries into one combined query
        
        Args:
            queries (List[str]): Natural language queries to merge
            embeddings (Optional[List[Dict]]): Pre-computed embeddings (not used)
        
        Returns:
            List[Dict]: Retrieved passages with metadata
        
        Time Target: 600-900ms total (vs 2400ms for 4 separate calls)
        """
        
        if not queries:
            logger.warning("No queries provided to retrieve_passages")
            return []
        
        start_time = time.time()
        
        # OPTIMIZATION 1: Merge all queries into ONE combined query
        merged_query = self._merge_queries(queries)
        
        logger.info(
            f"🚀 OPTIMIZED RAG: Single merged query from {len(queries)} enriched queries "
            f"(retrieve top_k={self.top_k}, rerank to top_{self.final_top_k})"
        )
        logger.debug(f"  Merged query: {merged_query[:120]}...")
        
        try:
            query_start = time.time()
            
            # SINGLE VERTEX CALL: Use rag.retrieval_query() ONCE
            response = rag.retrieval_query(
                rag_resources=[
                    rag.RagResource(
                        rag_corpus=self.corpus_resource_name,
                    )
                ],
                text=merged_query,
                similarity_top_k=self.top_k,  # Retrieve top 6
                vector_distance_threshold=self.similarity_threshold
            )
            
            query_time_ms = (time.time() - query_start) * 1000
            
            # Extract passages from contexts
            all_passages = self._extract_passages_from_response(
                response, merged_query, 0
            )
            
            logger.info(
                f"  Single query: {len(all_passages)} passages in {query_time_ms:.0f}ms"
            )
            
        except Exception as e:
            logger.error(f"  ❌ Merged query failed: {str(e)}")
            all_passages = []
        
        # Remove duplicates
        unique_passages = self._deduplicate_passages(all_passages)
        
        # OPTIMIZATION 2: Fast NumPy reranking (5-20ms)
        if len(unique_passages) > self.final_top_k:
            rerank_start = time.time()
            reranked_passages = self.reranker.rerank(
                passages=unique_passages,
                query=queries[0] if queries else merged_query,  # Use original question
                top_k=self.final_top_k
            )
            rerank_time_ms = (time.time() - rerank_start) * 1000
            logger.info(
                f"  ⚡ Fast rerank: {len(unique_passages)} → {len(reranked_passages)} "
                f"passages in {rerank_time_ms:.1f}ms"
            )
            unique_passages = reranked_passages
        
        total_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"✅ OPTIMIZED RAG complete! {len(unique_passages)} unique passages "
            f"in {total_time_ms:.0f}ms (saved ~{len(queries)-1}x network calls)"
        )
        
        return unique_passages
    
    def _merge_queries(self, queries: List[str]) -> str:
        """
        Merge multiple enriched queries into a single combined query
        
        Uses separator tokens to help RAG parse different subqueries
        while keeping total length reasonable (<2000 chars)
        
        Args:
            queries (List[str]): List of enriched query strings
        
        Returns:
            str: Combined query with separators
        """
        if len(queries) == 1:
            return queries[0]
        
        # Add explicit markers to help RAG parse different subqueries
        # Use ||| as separator (clear delimiter for text processing)
        merged = " ||| ".join(queries)
        
        # Truncate safely if too long (Vertex has limits)
        # Keep first 1800 chars to be safe (<2000 token limit)
        if len(merged) > 1800:
            merged = merged[:1800]
            logger.debug(f"  Truncated merged query to 1800 chars")
        
        return merged
    
    def _extract_passages_from_response(
        self,
        response,
        query: str,
        query_idx: int
    ) -> List[Dict]:
        """
        Extract passages from FAST rag.retrieval_query() response
        
        Args:
            response: rag.retrieval_query() response
            query (str): Original query
            query_idx (int): Query index
        
        Returns:
            List[Dict]: Extracted passages with metadata
        """
        passages = []
        
        try:
            # Response structure: response.contexts (RagContexts object)
            if not response or not hasattr(response, 'contexts'):
                logger.warning(f"    No contexts in response for query: {query[:60]}")
                return passages
            
            rag_contexts = response.contexts
            if not rag_contexts:
                logger.warning(f"    Empty contexts for query: {query[:60]}")
                return passages
            
            # RagContexts has a 'contexts' attribute which is a list
            contexts_list = []
            if hasattr(rag_contexts, 'contexts'):
                contexts_list = rag_contexts.contexts
            else:
                logger.warning(f"    RagContexts object has no 'contexts' attribute")
                return passages
            
            # Extract each context
            for idx, context in enumerate(contexts_list):
                text = ""
                source = "Classical Text"
                distance = 0.0
                
                # Extract text from source_chunks
                if hasattr(context, 'source_chunks') and context.source_chunks:
                    # Combine all chunks
                    chunk_texts = []
                    for chunk in context.source_chunks:
                        if hasattr(chunk, 'chunk') and hasattr(chunk.chunk, 'data'):
                            if hasattr(chunk.chunk.data, 'string_value'):
                                chunk_texts.append(chunk.chunk.data.string_value)
                        elif hasattr(chunk, 'text'):
                            chunk_texts.append(chunk.text)
                    text = " ".join(chunk_texts)
                elif hasattr(context, 'text'):
                    text = context.text
                
                # Extract source
                if hasattr(context, 'source_uri'):
                    source = context.source_uri.split('/')[-1]  # Get filename
                elif hasattr(context, 'source') and hasattr(context.source, 'title'):
                    source = context.source.title
                
                # Extract distance/score
                if hasattr(context, 'distance'):
                    distance = context.distance
                elif hasattr(context, 'score'):
                    # Score is similarity (higher = better), distance is opposite
                    distance = 1.0 - context.score
                
                # Convert distance to relevance score (0.0-1.0, higher = better)
                relevance_score = max(0.0, 1.0 - distance)
                
                if text:
                    passages.append({
                        "text": text,
                        "source": source,
                        "chapter": "",  # Not available in context
                        "verse": "",    # Not available in context
                        "relevance_score": relevance_score,
                        "query": query,
                        "query_index": query_idx,
                        "passage_index": idx
                    })
            
            logger.info(f"    Extracted {len(passages)} passages from {len(contexts_list)} contexts")
            
        except Exception as e:
            logger.error(f"    Failed to extract passages: {str(e)}")
            import traceback
            logger.error(f"    Traceback: {traceback.format_exc()}")
        
        return passages
    
    def _deduplicate_passages(self, passages: List[Dict]) -> List[Dict]:
        """
        Remove duplicate passages based on text content
        
        Args:
            passages (List[Dict]): List of passages
        
        Returns:
            List[Dict]: Deduplicated passages
        """
        seen_texts = set()
        unique_passages = []
        
        for passage in passages:
            text = passage.get("text", "")
            if text and text not in seen_texts:
                seen_texts.add(text)
                unique_passages.append(passage)
        
        if len(unique_passages) < len(passages):
            logger.info(
                f"  Removed {len(passages) - len(unique_passages)} duplicate passages"
            )
        
        return unique_passages
