"""
Vector Search Retriever Module
Purpose: Search pre-built embedding corpus using ScaNN algorithm
Retrieves semantically similar passages from classical astrology texts

Time: 15-30ms per query (very fast!)
"""

import json
import time
from typing import List, Dict, Optional, Tuple
import logging

# Google Cloud AI Platform imports
from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine import MatchingEngineIndexEndpoint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorSearchRetriever:
    """
    REAL Vector Search retriever using Vertex AI Vector Search with ScaNN
    Searches pre-built corpus of classical astrology texts
    
    Architecture:
    - Uses Vertex AI Matching Engine (Vector Search)
    - ScaNN algorithm for fast approximate nearest neighbor search
    - Searches embeddings stored in index
    - Returns actual classical text passages with metadata
    """
    
    def __init__(
        self,
        project_id: str,
        location: str,
        index_resource_name: Optional[str] = None,
        deployed_index_id: Optional[str] = None,
        index_endpoint_name: Optional[str] = None
    ):
        """
        Initialize REAL vector search retriever
        
        Args:
            project_id (str): Google Cloud project ID
            location (str): Region (e.g., "asia-south1")
            index_resource_name (str): Full path to Vector Search index
                Format: "projects/{project}/locations/{location}/indexes/{index_id}"
            deployed_index_id (str): ID of deployed index endpoint
            index_endpoint_name (str): Full path to index endpoint
                Format: "projects/{project}/locations/{location}/indexEndpoints/{endpoint_id}"
        """
        self.project_id = project_id
        self.location = location
        self.index_resource_name = index_resource_name
        self.deployed_index_id = deployed_index_id
        self.index_endpoint_name = index_endpoint_name
        
        # Vector Search client
        self.index_endpoint = None
        self.use_mock = False  # Flag to switch between real and mock
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Vertex AI Vector Search client"""
        try:
            # Initialize AI Platform
            aiplatform.init(project=self.project_id, location=self.location)
            
            # Check if index endpoint is configured
            if self.index_endpoint_name and self.deployed_index_id:
                try:
                    # Get the index endpoint
                    self.index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
                        index_endpoint_name=self.index_endpoint_name
                    )
                    
                    logger.info(
                        f"✅ Vector Search client initialized (REAL MODE). "
                        f"Endpoint: {self.index_endpoint_name}"
                    )
                    self.use_mock = False
                    
                except Exception as e:
                    logger.warning(
                        f"Could not connect to Vector Search endpoint: {e}. "
                        f"Falling back to MOCK mode."
                    )
                    self.use_mock = True
            else:
                logger.warning(
                    "Vector Search endpoint not configured. "
                    "Using MOCK mode. Set index_endpoint_name and deployed_index_id in config.py"
                )
                self.use_mock = True
                
        except Exception as e:
            logger.error(f"Failed to initialize Vector Search client: {str(e)}")
            logger.warning("Using MOCK mode as fallback")
            self.use_mock = True
    
    def search_passages(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 8,
        distance_threshold: float = 0.3,
        metric: str = "cosine"
    ) -> List[Dict]:
        """
        Search corpus for semantically similar passages
        
        REAL MODE: Searches Vertex AI Vector Search index
        MOCK MODE: Returns hardcoded passages (if index not available)
        
        Args:
            query_embeddings (List[List[float]]): List of embedding vectors (256-dim)
            top_k (int): Return top K similar passages (default 8)
            distance_threshold (float): Minimum similarity threshold (0.0-1.0)
            metric (str): Distance metric ("cosine", "euclidean", "dot_product")
        
        Returns:
            List[Dict]: Search results with passages
                [{
                    "query_index": 0,
                    "passages": [
                        {
                            "id": "bphs_7th_saturn_001",
                            "source": "BPHS Chapter 26",
                            "text": "Saturn as 7th lord gives...",
                            "chapter": "26",
                            "verse": "45",
                            "similarity_score": 0.92,
                            "rank": 1
                        },
                        ...
                    ],
                    "total_found": 5,
                    "execution_time_ms": 25.3
                }]
        
        Time Target: 15-30ms per query
        Cost: ~$0.0001 per query
        """
        
        start_time = time.time()
        
        # If mock mode, use fallback
        if self.use_mock:
            return self._search_passages_mock(
                query_embeddings, top_k, distance_threshold
            )
        
        # REAL MODE: Use Vertex AI Vector Search
        try:
            all_results = []
            
            logger.info(
                f"🔍 Searching Vector Search index for {len(query_embeddings)} queries. "
                f"Top-K: {top_k}, Threshold: {distance_threshold}"
            )
            
            for query_index, embedding in enumerate(query_embeddings):
                query_start = time.time()
                
                try:
                    # Search the deployed index
                    response = self.index_endpoint.find_neighbors(
                        deployed_index_id=self.deployed_index_id,
                        queries=[embedding],  # Single query
                        num_neighbors=top_k * 2,  # Get extra for filtering
                    )
                    
                    passages = []
                    
                    # Process matches
                    for neighbor in response[0]:  # First query result
                        # Calculate similarity score
                        similarity = self._distance_to_similarity(
                            neighbor.distance, 
                            metric
                        )
                        
                        # Filter by threshold
                        if similarity >= distance_threshold:
                            # Extract passage data from metadata
                            passage = {
                                "id": neighbor.id,
                                "text": neighbor.restricts.get("text", ""),
                                "source": neighbor.restricts.get("source", "Unknown"),
                                "chapter": neighbor.restricts.get("chapter", ""),
                                "verse": neighbor.restricts.get("verse", ""),
                                "topic": neighbor.restricts.get("topic", ""),
                                "similarity_score": similarity,
                                "distance": neighbor.distance,
                                "rank": len(passages) + 1
                            }
                            passages.append(passage)
                    
                    # Limit to top_k
                    passages = passages[:top_k]
                    
                    result = {
                        "query_index": query_index,
                        "passages": passages,
                        "total_found": len(passages),
                        "execution_time_ms": (time.time() - query_start) * 1000
                    }
                    
                    all_results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error searching query {query_index}: {e}")
                    # Return empty result for this query
                    all_results.append({
                        "query_index": query_index,
                        "passages": [],
                        "total_found": 0,
                        "error": str(e),
                        "execution_time_ms": (time.time() - query_start) * 1000
                    })
            
            total_time_ms = (time.time() - start_time) * 1000
            logger.info(
                f"✅ Vector search complete. "
                f"{len(query_embeddings)} queries searched in {total_time_ms:.0f}ms. "
                f"Avg: {total_time_ms/len(query_embeddings):.1f}ms per query"
            )
            
            return all_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            logger.warning("Falling back to mock mode")
            return self._search_passages_mock(
                query_embeddings, top_k, distance_threshold
            )
    
    def _search_passages_mock(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 8,
        distance_threshold: float = 0.3
    ) -> List[Dict]:
        """
        MOCK implementation for when Vector Search is not available
        Returns hardcoded classical passages for testing
        """
        
        start_time = time.time()
        all_results = []
        
        logger.warning("⚠️  Using MOCK classical passages (Vector Search not connected)")
        
        # Mock classical astrology passages for different query types
        mock_passages = {
            "appearance": [
                {
                    "id": "bphs_7th_saturn_001",
                    "source": "BPHS Chapter 26",
                    "chapter": "26",
                    "verse": "45-47",
                    "text": "Saturn as 7th lord gives lean physique, dark complexion, and serious demeanor. The native's spouse will be older in appearance, disciplined, and have prominent bone structure. They prefer traditional clothing and have a mature countenance.",
                    "similarity_score": 0.92
                },
                {
                    "id": "phaladeepika_venus_cap_002", 
                    "source": "Phaladeepika Chapter 8",
                    "chapter": "8",
                    "verse": "23-25",
                    "text": "Venus in Capricorn in 7th house creates attraction to mature, sophisticated partners. The spouse has elegant features, good skin, and prefers quality over quantity in appearance. They have natural grace and refined taste.",
                    "similarity_score": 0.89
                },
                {
                    "id": "brihat_jataka_darakaraka_003",
                    "source": "Brihat Jataka Chapter 5",
                    "chapter": "5", 
                    "verse": "12-14",
                    "text": "When Saturn is Darakaraka, the spouse exhibits Saturnian qualities - tall or medium height, well-defined jawline, serious expression. They age gracefully and have enduring beauty rather than flashy attractiveness.",
                    "similarity_score": 0.85
                },
                {
                    "id": "saravali_7th_house_004",
                    "source": "Saravali Chapter 18",
                    "chapter": "18",
                    "verse": "34-36",
                    "text": "The 7th lord's sign and nakshatra reveal the spouse's physical traits. Saturn influence gives darker skin, lean build, tall stature. Venus adds beauty and charm. Combinations determine the final appearance.",
                    "similarity_score": 0.83
                }
            ],
            "personality": [
                {
                    "id": "bphs_moon_cancer_004",
                    "source": "BPHS Chapter 15",
                    "chapter": "15",
                    "verse": "23-25",
                    "text": "Moon in Cancer creates emotional depth, nurturing nature, and strong intuition. The native is caring, protective of family, and has fluctuating moods like the Moon's phases. They prefer home comforts and security.",
                    "similarity_score": 0.91
                },
                {
                    "id": "light_on_life_d9_analysis_005",
                    "source": "Light on Life Chapter 12",
                    "chapter": "12",
                    "verse": "N/A",
                    "text": "D9 Ascendant reveals the inner spiritual nature and marriage karma. Strong D9 shows harmonious relationships and spiritual growth through partnership. The spouse becomes a catalyst for dharmic evolution.",
                    "similarity_score": 0.87
                },
                {
                    "id": "jataka_parijata_character_006",
                    "source": "Jataka Parijata Chapter 7",
                    "chapter": "7",
                    "verse": "56-58",
                    "text": "Saturn's influence on 7th house or lord makes the spouse serious, responsible, disciplined. They value duty and tradition. May be reserved emotionally but deeply loyal and committed to relationships.",
                    "similarity_score": 0.86
                }
            ],
            "timing": [
                {
                    "id": "phaladeepika_venus_dasha_006",
                    "source": "Phaladeepika Chapter 22",
                    "chapter": "22",
                    "verse": "12-15",
                    "text": "Venus Mahadasha brings marriage opportunities, especially when Venus is 7th lord or exalted. The most favorable periods are Venus-Jupiter, Venus-Mercury, and Venus-Moon bhuktis for relationship formation.",
                    "similarity_score": 0.94
                },
                {
                    "id": "bphs_jupiter_transit_007", 
                    "source": "BPHS Chapter 35",
                    "chapter": "35",
                    "verse": "67-70",
                    "text": "Jupiter's transit over 7th house or 7th lord activates marriage karma. When Jupiter aspects the Moon or Venus simultaneously, it creates highly auspicious timing for relationship commitment.",
                    "similarity_score": 0.88
                },
                {
                    "id": "saravali_dasha_timing_008",
                    "source": "Saravali Chapter 45",
                    "chapter": "45",
                    "verse": "23-26",
                    "text": "Marriage typically occurs during dasha of 7th lord, Venus, or planets placed in 7th. Saturn dasha may delay but gives stable, long-lasting unions. Jupiter dasha is most auspicious for marriage.",
                    "similarity_score": 0.91
                }
            ]
        }
        
        # Search for each query embedding  
        for query_index, embedding in enumerate(query_embeddings):
            query_start = time.time()
            
            # Rotate through passage types for variety
            passage_type = ["appearance", "personality", "timing"][query_index % 3]
            passages = mock_passages[passage_type]
            
            # Filter by threshold and limit to top_k
            filtered_passages = [
                {**p, "rank": i+1, "distance": 1.0 - p["similarity_score"]}
                for i, p in enumerate(passages)
                if p["similarity_score"] >= distance_threshold
            ][:top_k]
            
            result = {
                "query_index": query_index,
                "passages": filtered_passages,
                "total_found": len(filtered_passages),
                "execution_time_ms": (time.time() - query_start) * 1000,
                "mode": "MOCK"
            }
            
            all_results.append(result)
        
        total_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Mock search complete. "
            f"{len(query_embeddings)} queries in {total_time_ms:.0f}ms"
        )
        
        return all_results
    
    def search_with_filter(
        self,
        query_embeddings: List[List[float]],
        filters: Dict,
        top_k: int = 8,
        distance_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Search with metadata filters
        
        Args:
            query_embeddings (List[List[float]]): Query vectors
            filters (Dict): Metadata filters
            top_k (int): Number of results
            distance_threshold (float): Similarity threshold
        
        Returns:
            List[Dict]: Filtered search results
        """
        
        # Get all results first
        all_results = self.search_passages(
            query_embeddings=query_embeddings,
            top_k=top_k * 3,  # Get more for filtering
            distance_threshold=0.1  # Lower threshold, we'll filter more
        )
        
        # Apply filters
        filtered_results = []
        for result in all_results:
            filtered_passages = []
            
            for passage in result["passages"]:
                # Apply each filter condition
                matches = True
                
                for filter_key, filter_value in filters.items():
                    if filter_key == "source" and filter_value not in passage.get("source", ""):
                        matches = False
                        break
                
                if matches:
                    filtered_passages.append(passage)
            
            # Limit to top_k
            result["passages"] = filtered_passages[:top_k]
            result["total_after_filter"] = len(filtered_passages)
            
            filtered_results.append(result)
        
        return filtered_results
    
    def _distance_to_similarity(
        self,
        distance: float,
        metric: str = "cosine"
    ) -> float:
        """
        Convert distance to similarity score
        
        Args:
            distance (float): Raw distance from Vector Search
            metric (str): Distance metric used
        
        Returns:
            float: Similarity score (0.0-1.0)
        """
        
        if metric == "cosine":
            # Cosine distance to similarity: similarity = 1 - distance
            return max(0.0, 1.0 - distance)
        
        elif metric == "euclidean":
            # Euclidean: similarity = 1 / (1 + distance)
            return 1.0 / (1.0 + distance)
        
        elif metric == "dot_product":
            # Dot product: use as-is (already similarity)
            return distance
        
        else:
            return distance


# Usage example
if __name__ == "__main__":
    retriever = VectorSearchRetriever(
        project_id="superb-analog-464304-s0",
        location="asia-south1"
    )
    
    # Example query embeddings (would come from embeddings_retriever.py)
    query_embeddings = [
        [0.123] * 256,  # Saturn appearance query (mock)
        [0.234] * 256,  # Venus beauty query (mock)
    ]
    
    results = retriever.search_passages(
        query_embeddings=query_embeddings,
        top_k=8,
        distance_threshold=0.3
    )
    
    for result in results:
        print(f"Query {result['query_index']}: Found {result['total_found']} passages")
        for passage in result["passages"]:
            print(f"  - {passage['id']}: {passage['similarity_score']:.2f}")
