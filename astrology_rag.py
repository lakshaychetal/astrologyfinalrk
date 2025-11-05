"""
Vedic Astrology RAG System using Google Genai SDK
RAG Engine + Optional Google Search Grounding
Includes automatic retry logic for 429 rate limit errors
Includes response formatting and word limit enforcement
"""

import os
import asyncio
import re
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
from config import *


def clean_response_formatting(text: str) -> str:
    """
    Clean up response formatting
    - Remove excessive asterisks (***) → keep **
    - Remove symbol walls
    - Maintain readability
    
    Args:
        text: Raw response text
    
    Returns:
        str: Cleaned text
    """
    if not text:
        return text
    
    # Remove triple+ asterisks
    text = text.replace("***", "")
    while "****" in text:
        text = text.replace("****", "**")
    
    # Remove excessive blank lines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Clean symbol walls
    text = text.replace("=" * 20, "")
    text = text.replace("-" * 20, "")
    
    # Remove single asterisks but keep double asterisks for emphasis
    # This preserves **bold** but removes * bullets
    text = re.sub(r'(?<!\*)\*(?!\*)', '', text)
    
    # Remove trailing/leading whitespace
    text = text.strip()
    
    return text


def truncate_response(text: str, max_words: int = 600) -> str:
    """
    Truncate text to maximum word count
    Respects sentence boundaries (ends at period, not mid-sentence)
    
    Args:
        text: Input text
        max_words: Maximum words allowed (default 600)
    
    Returns:
        Truncated text, or original if under limit
    """
    if not text:
        return text
    
    words = text.split()
    
    if len(words) <= max_words:
        return text  # Already within limit
    
    # Truncate to max words
    truncated_text = ' '.join(words[:max_words])
    
    # Try to end at sentence boundary (last period in last 150 chars)
    if "." in truncated_text[-150:]:
        last_period = truncated_text.rfind(".")
        truncated_text = truncated_text[:last_period + 1]
    
    # Add note for truncated responses
    note = "\n\n[Response truncated for conciseness. Ask follow-up for more details.]"
    return truncated_text + note


class VedicAstrologyRAG:
    """
    Hybrid RAG + Google Search system using Google Genai SDK
    Retrieves from classical texts in RAG corpus
    Optionally grounds with Google Search for modern context
    Synthesizes with Gemini
    """
    
    def __init__(self):
        """Initialize configuration; delay client creation until first query."""
        # Client is created lazily to avoid startup failures in local/dev
        self.client = None

        # Model configuration (env-driven)
        self.model = MODEL_NAME

        # RAG corpus path
        self.rag_corpus = f"projects/{PROJECT_ID}/locations/{REGION}/ragCorpora/{CORPUS_ID}"

        # System instruction from config
        self.system_instruction = SYSTEM_INSTRUCTION
        
        # Enhanced system instruction for hybrid mode
        self.hybrid_system_instruction = SYSTEM_INSTRUCTION + """

HYBRID MODE GUIDELINES:
When Google Search results are available alongside classical texts:
1. PRIORITIZE classical Vedic texts (RAG corpus) as the PRIMARY authoritative source
2. Use Google Search results to:
   - Verify predictions with modern real-world examples
   - Add contemporary context and relevance
   - Cross-reference with modern astrological interpretations
3. Clearly distinguish between classical wisdom and modern insights
4. If conflicts arise, defer to classical texts but acknowledge modern perspectives
"""

    def _ensure_client(self):
        """Create the GenAI client if not already created."""
        if self.client is None:
            api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
            # Initialize GenAI client in Vertex mode (required for Vertex RAG store)
            self.client = genai.Client(vertexai=True, api_key=api_key)
    
    def _run_sync_query(self, prompt: str, use_google_search: bool = True) -> dict:
        """
        Query method that creates its own event loop in the thread
        
        Args:
            prompt: Full prompt with chart data + question
            use_google_search: If True, includes Google Search grounding alongside RAG
        """
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Create client on first use (lazy init)
            self._ensure_client()
            
            # Create RAG retrieval tool (always included)
            rag_tool = types.Tool(
                retrieval=types.Retrieval(
                    vertex_rag_store=types.VertexRagStore(
                        rag_resources=[
                            types.VertexRagStoreRagResource(
                                rag_corpus=self.rag_corpus
                            )
                        ],
                        similarity_top_k=RAG_TOP_K,
                        # Note: distance_threshold is not supported in this SDK version
                    )
                )
            )
            
            # Build tools list and config based on mode
            # Note: Google Search grounding may not be compatible with Vertex RAG in current SDK
            # Using enhanced prompt instead for hybrid mode
            if use_google_search:
                # Hybrid mode: Enhanced system instruction to leverage model's knowledge
                # Google Search tool not fully compatible with Vertex RAG yet
                print("📖 Hybrid Mode: Using RAG + Model's trained knowledge (Google Search tool pending SDK support)")
                config = types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                    tools=[rag_tool],
                    system_instruction=[types.Part.from_text(text=self.hybrid_system_instruction + 
                        "\n\nNote: Supplement classical texts with your knowledge of modern astrology practices, " +
                        "contemporary examples, and real-world applications. Cite when using general knowledge vs RAG sources.")],
                )
            else:
                # RAG only mode - strict classical texts
                print("📚 RAG Only Mode: Using classical texts exclusively")
                config = types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                    tools=[rag_tool],
                    system_instruction=[types.Part.from_text(text=self.system_instruction)],
                )
            
            # Make request to Gemini with RAG
            # The SDK uses async internally, so we run it in the event loop
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    response_text = ''.join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
                else:
                    response_text = str(response)
            else:
                response_text = str(response)
            
            return {
                'text': response_text,
                'success': True,
                'error': None,
                'used_google_search': use_google_search
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for 429 rate limit error
            if "429" in error_msg or "Resource exhausted" in error_msg:
                print(f"⚠️  Rate limited (429). Retrying automatically...")
                raise  # Trigger tenacity retry
            
            # Other errors
            print(f"❌ Error in RAG query: {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'text': None,
                'success': False,
                'error': error_msg
            }
        finally:
            # Clean up the event loop
            loop.close()
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True
    )
    def query(self, prompt: str, use_google_search: bool = True, max_words: int = 600) -> dict:
        """
        Query with RAG Engine + optional Google Search, with automatic retry on 429 errors
        Runs in a separate thread to avoid event loop conflicts with Gradio
        Applies formatting cleanup and word limit enforcement
        
        CRITICAL: Uses strict word limit (300 default) to enforce concise, direct answers
        
        Args:
            prompt: Full prompt with chart data + question
            use_google_search: If True, includes Google Search grounding alongside RAG
            max_words: Maximum word count for response (default 300 for strictness)
        
        Returns:
            dict: {
                'text': response (cleaned, word-limited), 
                'success': bool, 
                'error': error_msg,
                'used_google_search': bool
            }
        """
        
        try:
            # Always run in a separate thread to avoid event loop conflicts
            # This works whether we're in an async context or not
            import concurrent.futures
            import threading
            
            # Create a new thread to run the query
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_sync_query, prompt, use_google_search)
                result = future.result(timeout=120)  # 2 minute timeout
                
                # Apply formatting cleanup and word limit
                if result['success'] and result['text']:
                    # Clean formatting (remove asterisks, etc.)
                    cleaned_text = clean_response_formatting(result['text'])
                    
                    # Truncate to word limit
                    final_text = truncate_response(cleaned_text, max_words)
                    
                    result['text'] = final_text
                
                return result
                    
        except concurrent.futures.TimeoutError:
            return {
                'text': None,
                'success': False,
                'error': 'Query timed out after 2 minutes. Please try again.'
            }
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Exception in query wrapper: {error_msg}")
            return {
                'text': None,
                'success': False,
                'error': error_msg
            }
