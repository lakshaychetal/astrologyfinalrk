#!/usr/bin/env python3
"""
Quick RAG API Test
Tests if the RAG corpus retrieval is working
"""

import os
from google import genai
from google.genai import types

# Configuration from .env
PROJECT_ID = "superb-analog-464304-s0"
REGION = "asia-south1"
CORPUS_ID = "3379951520341557248"

def test_rag_retrieval():
    """Test RAG API with a simple query"""
    
    print("=" * 60)
    print("Testing Vertex AI RAG Retrieval")
    print("=" * 60)
    
    # Initialize client
    print(f"\n1. Initializing client...")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Region: {REGION}")
    print(f"   Corpus: {CORPUS_ID}")
    
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=REGION
    )
    print("   ✅ Client initialized")
    
    # Build corpus resource name
    corpus_resource_name = (
        f"projects/{PROJECT_ID}/locations/{REGION}/"
        f"ragCorpora/{CORPUS_ID}"
    )
    print(f"\n2. Corpus resource: {corpus_resource_name}")
    
    # Test query
    test_query = "Saturn in 7th house spouse appearance physical traits"
    print(f"\n3. Test query: '{test_query}'")
    
    # Try RAG retrieval
    print("\n4. Calling RAG API...")
    try:
        # Method 1: Using RAG Store with Tool (Simplified)
        rag_resource = types.VertexRagStoreRagResource(
            rag_corpus=corpus_resource_name
        )
        
        rag_store = types.VertexRagStore(
            rag_resources=[rag_resource]
            # Removed parameters causing validation errors
        )
        
        retrieval_tool = types.Tool(
            retrieval=types.Retrieval(
                vertex_rag_store=rag_store
            )
        )
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Find relevant classical astrology passages about: {test_query}",
            config=types.GenerateContentConfig(
                temperature=0.0,
                tools=[retrieval_tool],
                max_output_tokens=1024
            )
        )
        
        print("   ✅ RAG API call successful!")
        
        # Check response
        print("\n5. Response Analysis:")
        print(f"   - Response type: {type(response)}")
        print(f"   - Has text: {hasattr(response, 'text')}")
        print(f"   - Has grounding_metadata: {hasattr(response, 'grounding_metadata')}")
        
        if hasattr(response, 'text') and response.text:
            print(f"\n   Response text (first 500 chars):")
            print(f"   {response.text[:500]}...")
        
        if hasattr(response, 'grounding_metadata'):
            metadata = response.grounding_metadata
            print(f"\n   Grounding metadata:")
            print(f"   - Type: {type(metadata)}")
            
            if hasattr(metadata, 'grounding_chunks'):
                chunks = metadata.grounding_chunks
                print(f"   - Chunks found: {len(chunks) if chunks else 0}")
                
                if chunks:
                    print(f"\n   First chunk:")
                    chunk = chunks[0]
                    print(f"   - Type: {type(chunk)}")
                    if hasattr(chunk, 'retrieved_context'):
                        ctx = chunk.retrieved_context
                        if hasattr(ctx, 'text'):
                            print(f"   - Text: {ctx.text[:200]}...")
                        if hasattr(ctx, 'title'):
                            print(f"   - Source: {ctx.title}")
            
            if hasattr(metadata, 'retrieval_metadata'):
                print(f"   - Has retrieval metadata: Yes")
        
        print("\n" + "=" * 60)
        print("✅ RAG TEST SUCCESSFUL!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ RAG API Error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Try to get more details
        if hasattr(e, '__dict__'):
            print(f"   Error details: {e.__dict__}")
        
        print("\n" + "=" * 60)
        print("❌ RAG TEST FAILED")
        print("=" * 60)
        
        return False

if __name__ == "__main__":
    success = test_rag_retrieval()
    exit(0 if success else 1)
