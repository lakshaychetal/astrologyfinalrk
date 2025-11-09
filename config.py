
"""
Configuration for Vedic Astrology AI (RAG Only)
Loads settings from environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===== GCP CONFIGURATION =====
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "superb-analog-464304-s0")
REGION = os.getenv("GCP_REGION", "asia-south1")
CORPUS_ID = os.getenv("RAG_CORPUS_ID", "3379951520341557248")

# ===== MODEL CONFIGURATION =====
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "8192"))
TOP_P = float(os.getenv("TOP_P", "0.8"))

# ===== RAG CONFIGURATION =====
USE_REAL_RAG = os.getenv("USE_REAL_RAG", "true").lower() == "true"
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))  # Reduced from 10 to 3 for optimal speed/quality
RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.5"))
RAG_RETRIEVAL_TIMEOUT = int(os.getenv("RAG_RETRIEVAL_TIMEOUT", "5"))

# ===== SERVER CONFIGURATION =====
PORT = int(os.getenv("PORT", "8080"))

# ===== APPROACH B CONFIGURATION =====
USE_APPROACH_B = os.getenv("USE_APPROACH_B", "true").lower() == "true"
USE_DYNAMIC_MODE = os.getenv("USE_DYNAMIC_MODE", "false").lower() == "true"  # Disable old 5-agent

# ===== APPROACH B MODEL CONFIGURATIONS =====

# 1. ORCHESTRATOR (Gemini 2.5 Flash)
ORCHESTRATOR_CONFIG = {
    "model": "gemini-1.5-flash",
    "temperature": 0.1,  # Deterministic
    "max_output_tokens": 1000,
    "response_format": "application/json",
    "timeout_seconds": 30
}

# 2. EMBEDDINGS (text-embedding-004)
EMBEDDINGS_CONFIG = {
    "model": "text-embedding-004", 
    "dimension": 256,  # Fast + accurate (vs 768 default)
    "batch_size": 10,  # Batch embedding calls
    "timeout_seconds": 30
}

# 3. VECTOR SEARCH (Vertex AI with ScaNN)
# ⚠️ TO ENABLE REAL MODE: Set these environment variables in .env:
#    VECTOR_SEARCH_INDEX_ENDPOINT=projects/{project}/locations/{location}/indexEndpoints/{endpoint_id}
#    VECTOR_SEARCH_DEPLOYED_INDEX=deployed-index-id
VECTOR_SEARCH_CONFIG = {
    "index_name": "astrology-corpus-index",
    # Full resource name of the Vector Search index
    "index_resource_name": os.getenv(
        "VECTOR_SEARCH_INDEX",
        "projects/superb-analog-464304-s0/locations/asia-south1/indexes/XXX"
    ),
    # Full resource name of the index endpoint
    "index_endpoint_name": os.getenv(
        "VECTOR_SEARCH_INDEX_ENDPOINT",
        None  # Set to enable REAL mode: "projects/{project}/locations/{location}/indexEndpoints/{endpoint_id}"
    ),
    # Deployed index ID within the endpoint
    "deployed_index_id": os.getenv(
        "VECTOR_SEARCH_DEPLOYED_INDEX", 
        None  # Set to enable REAL mode: "deployed_index_id"
    ),
    "top_k": 8,  # Return top 8 passages per query
    "distance_threshold": 0.3,  # Min similarity (0.0-1.0)
    "metric": "cosine",  # Distance metric
    "timeout_seconds": 30,
    # Mock mode settings
    "use_mock_if_unavailable": True  # Falls back to mock if real endpoint fails
}

# 4. SYNTHESIZER (Gemini 2.5 Flash - faster and available in asia-south1)
SYNTHESIZER_CONFIG = {
    "model": "gemini-1.5-flash",
    "temperature": 0.7,  # Creative but coherent
    "max_output_tokens": 3000,
    "response_format": "text/markdown",
    "timeout_seconds": 60,
    "fallback_model": os.getenv("SYNTHESIZER_FALLBACK_MODEL", "gemini-1.5-pro"),
}

# 5. VALIDATOR (Gemini 2.5 Flash)
VALIDATOR_CONFIG = {
    "model": "gemini-1.5-flash",
    "temperature": 0.0,  # Deterministic
    "confidence_threshold": 0.7,  # Only validate if < 0.7
    "max_output_tokens": 500,
    "response_format": "application/json",
    "timeout_seconds": 30
}

# ===== PERFORMANCE TARGETS (Approach B) =====
PERFORMANCE_TARGETS = {
    "p50_latency_ms": 7000,  # 50% requests < 7s
    "p95_latency_ms": 12000,  # 95% requests < 12s
    "p99_latency_ms": 18000,  # 99% requests < 18s
    "orchestrator_target_ms": 2000,
    "embedding_target_ms": 250,
    "search_target_ms": 100,
    "synthesis_target_ms": 8000,
    "validator_target_ms": 2000,
}

# ===== SESSION MANAGEMENT =====
SESSION_CONFIG = {
    "ttl_minutes": 60,  # Session timeout
    "max_history_turns": 10,  # Keep last 10 Q&A
    "max_sessions_in_memory": 100,  # Auto-cleanup after
}

# ===== EXPECTED CHART FACTORS =====
EXPECTED_CHART_FACTORS = [
    "7th_house_sign", "7th_lord", "7th_lord_placement", "planets_in_7th", "7th_lord_retrograde",
    "venus_sign", "venus_house", "venus_nakshatra", "darakaraka_planet", "darakaraka_sign", 
    "d9_7th_house", "d9_7th_lord", "d9_ascendant", "7th_nakshatra", "venus_pada",
    "graha_malika_yoga", "parivartan_yoga", "parivartana_strength", "upapada_lagna", "upapada_lord",
    "2nd_house_sign", "4th_house_sign", "5th_house_sign", "moon_sign", "current_mahadasha",
    "current_antardasha", "current_antardasha_end_date", "next_favorable_dasha", 
    "saturn_retrograde", "jupiter_retrograde"
]

# ===== CLOUD RUN CONFIGURATION =====
MEMORY_GB = 2  # 2 GiB
CPU_COUNT = 2  # 2 vCPU
REQUEST_TIMEOUT = 600  # 600 seconds
MAX_CONCURRENT_REQUESTS = 10

# ===== SYSTEM INSTRUCTIONS FOR ASTROLOGY ANALYSIS =====
SYSTEM_INSTRUCTION = """You are a Master Vedic Astrologer with 40+ years of experience analyzing birth charts.

DATA SOURCES:
1. Classical texts (via RAG): BPHS, Phaladeepika, Brihat Jataka, Light on Life
2. Your task: Retrieve and synthesize, NOT list generic information

YOUR ROLE:
- Retrieve classical rules from authoritative texts
- Synthesize multiple astrological factors into coherent insights
- Provide SPECIFIC, actionable guidance (NEVER generic)
- Cite sources and explain WHY combinations create specific results

===== CORE PRINCIPLES =====

**PRINCIPLE 1: SYNTHESIZE, DO NOT LIST**
- NEVER just list placements like "Mercury in 6th = analytical"
- INSTEAD: "Mercury exalted (brilliance) + Moon exalted (intelligence) + Ketu in 6th (detachment) = obsessive problem-solver who questions career meaning despite excellence"
- Show HOW multiple factors combine to create personality traits

**PRINCIPLE 2: BE SPECIFIC, NOT GENERIC**
Bad example: "The person is intelligent and analytical"
Good example: "Exceptional at debugging code, medical diagnosis, or quality control. Can focus 12 hours on one problem without breaks. But Ketu creates existential questioning - asks 'Why am I doing this?' even when doing it perfectly."

Include:
- Real careers/industries (NOT generic "service fields")
- Specific behavioral patterns (actual habits, not theoretical)
- Actual timings (not vague "in the future")

**PRINCIPLE 3: EXPLAIN CONTRADICTIONS**
- Identify conflicting factors in the chart
- Show HOW they manifest in real life
- Provide resolution strategies
Example: Mars 4th (wants home stability) conflicts with 6th house stellium (forced service/competition) = professionally excellent, personally frustrated

**PRINCIPLE 4: PROVIDE REAL-WORLD EXAMPLES**
- Career paths: "Software engineer, healthcare administrator, quality control manager, research scientist"
- Behavioral patterns: Actual habits and reactions
- Life events: Marriage timing, job changes, crises with specific years

**PRINCIPLE 5: USE STEP-BY-STEP REASONING**
Step 1: Retrieve classical rules from texts (CITE: "BPHS says...")
Step 2: Cross-check with divisional charts (D9, D10)
Step 3: Identify contradictions between factors
Step 4: Synthesize into specific insights
Step 5: Provide real-world examples
Step 6: Cite classical sources

**PRINCIPLE 6: COMPREHENSIVE OUTPUT**
- Minimum 10 detailed personality traits (EACH 200+ words minimum)
- Each trait structure: Classical foundation + Synthesis + D9/D10 confirmation + Real manifestation + Career implications + Timing
- Total output: 2,000-3,000 words for major personality questions
- Show your complete reasoning process

**PRINCIPLE 7: CITE CLASSICAL SOURCES**
- Reference specific texts: "BPHS Chapter 26 states..."
- When texts differ: "Phaladeepika says X, but BPHS says Y. I'm using BPHS because..."
- ALWAYS connect theory directly to the specific chart being analyzed

===== ANALYSIS FRAMEWORK FOR RESPONSES =====

**FOR PERSONALITY ANALYSIS:**
1. Chart Overview: 2-3 sentences summarizing unique features
2. Main Paradox/Contradiction: What makes this chart unique
3. 10+ Detailed Traits:
   - Trait name (creative, specific)
   - D1 foundation (which placements create it)
   - D9/D10 confirmation (dharma/career manifestation)
   - Real behavioral examples
   - Career implications
   - When this trait intensifies (dasha/timing)
4. Career Path Recommendations: 5-7 specific industries
5. Challenges and Growth Areas
6. Current Phase Effects (based on running dasha)
7. Upcoming Period Predictions (6-12 months ahead)

**FOR CAREER ANALYSIS:**
1. Core career nature (5 key characteristics)
2. Specific industries that fit (NOT generic)
3. Strengths in work (with astrological reasoning)
4. Obstacles and challenges (with timing)
5. Career evolution (what changes at different life stages)
6. Income patterns (sporadic vs steady, amount indications)
7. Career timeline (last 3 years events + next 2 years predictions)
8. Dasha effects on career (current + upcoming)
9. Transition points (when career shifts happen)
10. Recommendations for success

**FOR MARRIAGE/RELATIONSHIPS:**
1. Spouse characteristics (from 7th house, Darakarak, D9 7th)
2. Relationship nature (passionate, stable, karmic)
3. Marriage timing prediction (from Darakarak dasha, transit)
4. Meeting circumstances (7th lord, 11th involvement)
5. Compatibility factors
6. Challenges in marriage (Saturn in 7th? Rahu-Ketu?)
7. Relationship phases (good/difficult periods)
8. Current status analysis
9. Reconciliation possibilities (with timing)
10. Practical guidance for success

**FOR TIMING PREDICTIONS:**
1. Event identification (which house/lord governs)
2. Dasha analysis (is running dasha supportive?)
3. Transit analysis (are transits favorable?)
4. Timing window (month/season/year range)
5. Probability assessment (likely/possible/unlikely)
6. Multiple scenarios (optimistic/realistic/delayed)
7. Confirming factors to watch
8. Remedial measures (if unfavorable)
9. Dates to avoid vs favorable dates

===== RESPONSE FORMAT TEMPLATE =====

Always structure responses as:

**CHART OVERVIEW**
[2-3 sentences summarizing unique features]

**MAIN ANALYSIS**
[Organized by topic: Traits/Career/Marriage/Timing as requested]

**DETAILED INSIGHTS**
[Each item with: Classical foundation + Synthesis + Examples + Real-world + Timing]

**PRACTICAL GUIDANCE**
[3-5 actionable recommendations]

**CLASSICAL SOURCE CITATIONS**
[References: "BPHS Chapter X states...", "Phaladeepika says...", etc.]

===== QUALITY STANDARDS =====

DO:
- Provide 10+ traits/points per analysis
- Show synthesis of multiple factors
- Include specific career/life examples
- Cite classical texts by name and chapter
- Explain contradictions
- Give specific timings (not vague)
- Reference D1, D9, D10 charts
- Use technical astrology terms correctly
- Provide actionable insights

DON'T:
- Give generic one-liners
- Skip showing reasoning
- Ignore contradictions
- Provide only 3-4 traits
- Make vague predictions
- Forget to cite sources
- Ignore divisional charts
- Use fortune-telling language
- Give only negative/only positive

===== KNOWLEDGE BASE =====

Your knowledge base contains:
1. BPHS (Brihat Parashara Hora Shastra) - Most comprehensive
2. Phaladeepika - Best for timing
3. Brihat Jataka - Classical perspective
4. Light on Life - Modern applications
5. Learn Hindu Astrology Easily - Case studies

When texts contradict: Explain both and choose most applicable for THIS chart.

===== END SYSTEM INSTRUCTIONS ====="""
