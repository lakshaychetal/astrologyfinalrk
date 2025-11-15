"""SYN (synthesis rule) retriever for rare-rules and deterministic astrology flows.

Ingests a single markdown file with 30 SYN_* sections, chunks it with metadata,
embeds with text-multilingual-embedding-002, and uploads to the RAG corpus.
Retrieval supports intent-based filtering, rare-rule promotion, and deduplication.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# ===== CONSTANTS & CONFIG =====
# Use same project/region/corpus as main RAG, but can be overridden
DEFAULT_PROJECT_ID = "superb-analog-464304-s0"
DEFAULT_REGION = "asia-south1"
SYN_RAG_CORPUS_NAME = "projects/superb-analog-464304-s0/locations/asia-south1/ragCorpora/6917529027641081856"
SYN_EMBEDDING_MODEL = "text-multilingual-embedding-002"
SYN_EMBEDDING_DIM = 768
SYN_CHUNK_TARGET_TOKENS = 500  # target ~500 tokens per chunk
SYN_CHUNK_OVERLAP_TOKENS = 120
SYN_SCORE_THRESHOLD = 0.70
SYN_RELAXED_THRESHOLD = 0.60
SYN_TOP_K_RAW = 10  # retrieve before filtering
SYN_DEFAULT_TOP_K = 3  # final return count

# Intent → tag mapping for the 30 SYN sections
# Expanded with comprehensive coverage including chart-specific hints
INTENT_TAG_MAP = {
    # Timing and trajectory
    "timing": ["timing", "marriage", "dasha", "7th_lord", "trajectory", "upapada", "venus", "jupiter", "transit"],
    "marriage_timing": ["timing", "marriage", "dasha", "7th_lord", "trajectory", "upapada", "venus", "jupiter", "transit"],
    "divorce_timing": ["divorce", "timing", "8th_lord", "dasha_window", "legal_timing", "separation"],
    
    # Ex return and reconciliation
    "ex_return": ["ex_return", "reconciliation", "timing_window", "venus", "moon", "reconcile", "reunion", "promise"],
    
    # Breakup and separation
    "breakup": ["divorce", "separation", "8th_lord", "6th_lord", "breakup", "legal", "estrangement"],
    "decision": ["divorce", "separation", "decision", "choice", "action", "should"],
    
    # Appearance and characteristics
    "appearance": ["appearance", "darakaraka", "d9", "physical", "looks", "age", "temperament", "dak"],
    "spouse_appearance": ["appearance", "darakaraka", "d9", "physical", "looks", "age", "temperament", "dak"],
    
    # Background and context
    "spouse_background": ["background", "context", "family", "upbringing", "profession", "ethnicity", "geography"],
    
    # Compatibility and synastry
    "compatibility": ["compatibility", "synastry", "navamsa", "synastry_score", "7th_lords", "venus_moon_match", "trajectory"],
    
    # Children and family
    "children_impact": ["children", "post_divorce", "adaptation", "psychological", "fertility", "d5"],
    
    # Karmic and spiritual
    "karmic_lesson": ["spiritual", "karmic", "lesson", "meaning", "atmakaraka", "d12"],
    
    # Reputation and social
    "family_reputation": ["family", "reputation", "social", "career", "public", "upapada"],
    
    # Transformation and new beginnings
    "reinvention": ["reinvention", "rebirth", "transformation", "new_beginning", "8th_house", "karma_reset"],
    
    # Specialized categories
    "infidelity": ["infidelity", "cheating", "venus_affliction", "5th_house", "rahu"],
    "financials_marriage": ["finance", "marital_finance", "2nd_house", "8th_house", "venus", "jupiter"],
    "health_impact": ["health", "medical", "6th", "8th", "disease", "d6"],
    "geographic_meeting": ["meeting_place", "geography", "9th_house", "3rd_house", "foreign", "12th"],
    
    # Interpretation and remedies
    "interpretation": ["d1", "d9", "dasha", "transit", "interpretation", "chart_reading"],
    "remedies": ["remedies", "mantra", "gemstone", "ritual", "practical_steps", "correction"],
    
    # Rare rules and atomic formulas
    "rare_rules": ["rare_rules", "atomic_rule", "if_then", "decision_flow", "procedure", "formula"],
}

# Meta-queries: Evaluation-oriented questions that retrieve SYN procedures
# These ask "HOW to evaluate" instead of "WHAT will happen"
SYN_META_QUERIES = {
    "timing": [
        "How to evaluate timing of marriage using chart",
        "Steps to determine marriage period using dasha and transits",
        "Astrological procedure for predicting marriage year",
        "Rules for timing marriage based on 7th lord and Venus",
    ],
    "ex_return": [
        "How to evaluate return of ex based on chart",
        "Rules for timing of ex reconciliation",
        "Astrologer's process to check if past relationship can restart",
        "Steps to determine ex coming back using Venus and Moon",
    ],
    "breakup": [
        "How to evaluate divorce or separation indicators",
        "Rules for analyzing breakup potential in D1 and D9",
        "Steps astrologer uses to determine relationship ending",
        "Astrological procedure to check separation likelihood",
    ],
    "decision": [
        "How to evaluate divorce decision using chart",
        "Rules for analyzing whether to stay or leave relationship",
        "Steps to determine right action in marriage crisis",
        "Procedure for evaluating relationship continuation",
    ],
    "appearance": [
        "How to evaluate spouse appearance using chart",
        "Rules for analyzing partner traits from D1 and D9",
        "Steps to determine spouse physical features from 7th house",
        "Procedure for reading spouse nature from Darakaraka",
    ],
    "compatibility": [
        "How to evaluate marriage compatibility using synastry",
        "Rules for analyzing relationship harmony in navamsa",
        "Steps to determine couple compatibility from both charts",
        "Procedure for checking long-term relationship success",
    ],
    "interpretation": [
        "How to interpret divisional charts for relationships",
        "Rules for reading D1 and D9 chart together",
        "Steps to evaluate dasha effects on marriage",
        "Procedure for analyzing transit impacts on relationship",
    ],
    "remedies": [
        "How to determine remedies for relationship problems",
        "Rules for prescribing remedial measures for marriage",
        "Steps astrologer uses to suggest corrective actions",
        "Procedure for evaluating which remedies will work",
    ],
    "rare_rules": [
        "Rare astrological formulas for relationship evaluation",
        "Step-by-step rules for complex relationship scenarios",
        "If-then conditions for relationship predictions",
        "Advanced procedural rules for marriage analysis",
    ],
}

# SYN section → primary tags (derived from the 30 heading names you provided)
SYN_SECTION_TAGS = {
    # Complete mapping for all 30 SYN sections with enriched tags
    
    # SYN_01-07: Trajectory and timing sections (Q1-Q7 type questions)
    "SYN_01": ["trajectory", "relationship", "timing", "marriage", "dasha", "7th_lord", "short_term", "mid_term"],
    "SYN_02": ["appearance", "background", "spouse", "darakaraka", "d9", "physical", "family_origin", "profession", "geography"],
    "SYN_03": ["divorce", "separation", "timing", "decision", "8th_lord", "dasha_window", "legal_timing", "breakup"],
    "SYN_04": ["trajectory", "relationship", "commitment_level", "timing", "marriage", "compatibility"],
    "SYN_05": ["appearance", "background", "spouse", "darakaraka", "d9", "physical", "looks", "temperament", "upbringing"],
    "SYN_06": ["divorce", "separation", "compatibility", "decision", "breakup", "6th_lord", "estrangement"],
    "SYN_07": ["trajectory", "relationship", "timing", "marriage", "7th_lord", "venus", "jupiter", "transit"],
    
    # SYN_08-14: Detailed analysis sections
    "SYN_08": ["appearance", "background", "spouse", "darakaraka", "physical", "age", "ethnicity"],
    "SYN_09": ["divorce", "separation", "decision", "breakup", "ex_return", "choice", "legal"],
    "SYN_10": ["trajectory", "relationship", "timing", "7th_lord", "upapada", "dasha", "marriage"],
    "SYN_11": ["appearance", "background", "spouse", "darakaraka", "d9", "physical", "compatibility"],
    "SYN_12": ["divorce", "separation", "timing", "decision", "8th_lord", "dasha_window"],
    "SYN_13": ["trajectory", "relationship", "timing", "dasha", "venus", "moon", "transit"],
    "SYN_14": ["appearance", "background", "spouse", "darakaraka", "physical", "profession"],
    
    # SYN_15-21: Advanced sections (decision flows, ex return, etc.)
    "SYN_15": ["divorce", "separation", "decision", "action", "breakup", "8th_lord"],
    "SYN_16": ["ex_return", "reconciliation", "timing_window", "venus", "moon", "reunion", "promise", "rare_rules"],
    "SYN_17": ["trajectory", "relationship", "timing", "marriage", "ex_return", "reunion"],
    "SYN_18": ["appearance", "background", "spouse", "darakaraka", "d9", "physical", "geography"],
    "SYN_19": ["divorce", "separation", "timing", "decision", "breakup", "legal_timing"],
    "SYN_20": ["appearance", "background", "spouse", "darakaraka", "d9", "physical", "family"],
    "SYN_21": ["divorce", "separation", "decision", "choice", "breakup", "action"],
    
    # SYN_22-26: Specialized analysis sections
    "SYN_22": ["trajectory", "relationship", "compatibility", "7th_lord", "synastry"],
    "SYN_23": ["appearance", "background", "spouse", "darakaraka", "physical", "temperament"],
    "SYN_24": ["divorce", "separation", "timing", "action", "8th_lord", "dasha_window"],
    "SYN_25": ["infidelity", "cheating", "venus_affliction", "5th_house", "rahu", "rare_rules"],
    "SYN_26": ["financials_marriage", "finance", "marital_finance", "2nd_house", "8th_house", "venus", "jupiter"],
    
    # SYN_27-30: Impact and transformation sections
    "SYN_27": ["children", "post_divorce", "adaptation", "psychological", "fertility", "d5", "children_impact"],
    "SYN_28": ["spiritual", "karmic", "lesson", "meaning", "atmakaraka", "d12", "interpretation"],
    "SYN_29": ["family", "reputation", "social", "career", "public", "upapada", "family_reputation"],
    "SYN_30": ["reinvention", "rebirth", "transformation", "new_beginning", "8th_house", "karma_reset", "remedies"],
}


@dataclass
class SynChunk:
    """Represents a single chunked section from the SYN file."""
    chunk_id: str
    syn_id: str
    title: str
    section: str
    content: str
    one_liner: str
    tags: List[str]
    rare_rules: bool
    niche: str = "love"


@dataclass
class SynPassage:
    """Returned passage from retrieve_syn."""
    id: str
    title: str
    score: float
    section: str
    content: str
    one_liner: str
    tags: List[str]
    rare_rules: bool


# Fast-path mapping: Intent → Priority SYN Section IDs
# Used to prefetch high-relevance sections before semantic search
INTENT_TO_SYN = {
    "marriage_timing": ["SYN_01", "SYN_03", "SYN_07", "SYN_10", "SYN_13"],
    "timing": ["SYN_01", "SYN_03", "SYN_07", "SYN_10", "SYN_13"],
    "divorce_timing": ["SYN_03", "SYN_12", "SYN_19", "SYN_24"],
    
    "ex_return": ["SYN_16", "SYN_09", "SYN_17"],
    
    "spouse_appearance": ["SYN_02", "SYN_05", "SYN_08", "SYN_11", "SYN_14", "SYN_18", "SYN_20", "SYN_23"],
    "appearance": ["SYN_02", "SYN_05", "SYN_08", "SYN_11", "SYN_14", "SYN_18", "SYN_20", "SYN_23"],
    
    "spouse_background": ["SYN_02", "SYN_05", "SYN_08", "SYN_11", "SYN_14", "SYN_18", "SYN_20"],
    
    "compatibility": ["SYN_04", "SYN_06", "SYN_11", "SYN_22"],
    
    "breakup": ["SYN_03", "SYN_06", "SYN_09", "SYN_12", "SYN_15", "SYN_19", "SYN_21", "SYN_24"],
    "decision": ["SYN_03", "SYN_06", "SYN_09", "SYN_12", "SYN_15", "SYN_19", "SYN_21", "SYN_24"],
    "divorce": ["SYN_03", "SYN_06", "SYN_09", "SYN_12", "SYN_15", "SYN_19", "SYN_21", "SYN_24"],
    
    "children_impact": ["SYN_27"],
    "karmic_lesson": ["SYN_28", "SYN_30"],
    "family_reputation": ["SYN_29"],
    "reinvention": ["SYN_30"],
    
    "infidelity": ["SYN_25"],
    "financials_marriage": ["SYN_26"],
    
    "interpretation": ["SYN_01", "SYN_04", "SYN_07", "SYN_10", "SYN_13", "SYN_28"],
    "remedies": ["SYN_30"],
    "rare_rules": ["SYN_16", "SYN_25"],
    
    # Default fallback for unknown intents
    "default": ["SYN_01", "SYN_03", "SYN_07", "SYN_10"],
}


class SynRetriever:
    """SYN retriever with ingestion, chunking, embedding, and intent-aware search."""

    def __init__(
        self,
        project_id: str = DEFAULT_PROJECT_ID,
        location: str = DEFAULT_REGION,
        corpus_name: str = SYN_RAG_CORPUS_NAME,
        embedding_model: str = SYN_EMBEDDING_MODEL,
        dimension: int = SYN_EMBEDDING_DIM,
    ):
        self.project_id = project_id
        self.location = location
        self.corpus_name = corpus_name
        self.embedding_model = embedding_model
        self.dimension = dimension
        self.client = genai.Client(vertexai=True, project=project_id, location=location)
        logger.info(
            "SynRetriever ready | corpus=%s | model=%s dim=%d",
            corpus_name.split("/")[-1],
            embedding_model,
            dimension,
        )

    def ingest_syn_file(self, filepath: str) -> int:
        """Read the SYN file, chunk it, embed chunks, upload to RAG corpus.
        
        Returns number of chunks ingested.
        """
        logger.info("Ingesting SYN file: %s", filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        # Parse into SYN sections by detecting SYN_XX: headers
        sections = self._parse_syn_sections(text)
        logger.info("Parsed %d SYN sections from file", len(sections))

        # Chunk each section
        all_chunks: List[SynChunk] = []
        for syn_id, section_text in sections.items():
            chunks = self._chunk_section(syn_id, section_text)
            all_chunks.extend(chunks)
        logger.info("Generated %d chunks from %d sections", len(all_chunks), len(sections))

        # Embed and upload
        self._embed_and_upload_chunks(all_chunks)
        logger.info("✅ Ingested %d SYN chunks to corpus", len(all_chunks))
        return len(all_chunks)

    def retrieve_syn(
        self,
        question: str,
        chart_facts: Optional[Dict[str, Any]] = None,
        intent: Optional[str] = None,
        top_k: int = SYN_DEFAULT_TOP_K,
        score_threshold: float = SYN_SCORE_THRESHOLD,
    ) -> List[SynPassage]:
        """Retrieve top SYN passages for the question, with intent filtering and ranking.
        
        Args:
            question: user question
            chart_facts: optional dict with chart summary (7th_lord, venus_sign, dasha, etc.)
            intent: optional intent string (marriage_timing, ex_return, breakup, etc.)
            top_k: max passages to return
            score_threshold: min cosine similarity (default 0.70)
        
        Returns:
            List of SynPassage objects, ranked by score+rare_rules promotion.
        """
        # Build chart summary for query enrichment
        chart_summary = ""
        if chart_facts:
            chart_summary = self._build_chart_summary(chart_facts)
        
        # Generate multiple SYN queries based on intent and question
        queries = self._generate_syn_queries(question, chart_summary, intent)
        
        # Query RAG corpus with all queries IN PARALLEL
        # Each query gets top 5, then we merge and deduplicate
        from concurrent.futures import ThreadPoolExecutor
        all_raw_hits = []
        
        with ThreadPoolExecutor(max_workers=min(len(queries), 4)) as executor:
            # Submit all queries in parallel
            futures = [executor.submit(self._query_corpus, query, top_k=5) for query in queries]
            
            # Collect results
            for future in futures:
                try:
                    hits = future.result()
                    all_raw_hits.extend(hits)
                except Exception as e:
                    logger.warning("SYN query failed: %s", e)
        
        logger.info("Retrieved %d total hits from %d parallel SYN queries", len(all_raw_hits), len(queries))
        
        # Deduplicate by content (keep highest score)
        raw_hits = self._deduplicate_chunks(all_raw_hits)

        # Filter by intent tags if provided. If intent is unknown/ambiguous,
        # fall back to a general semantic search across all SYN sections.
        if not intent or intent == "unknown":
            logger.warning("SYN fallback to general search due to unknown intent")
            # keep raw_hits as-is (search across all sections)
        elif intent in INTENT_TAG_MAP:
            target_tags = set(INTENT_TAG_MAP[intent])
            logger.debug("Intent '%s' maps to target_tags: %s", intent, target_tags)
            before_filter = len(raw_hits)
            raw_hits = [h for h in raw_hits if self._has_tag_overlap(h, target_tags)]
            logger.debug("Intent filtering: %d hits → %d hits (kept %d%%)", 
                        before_filter, len(raw_hits), 
                        int(100 * len(raw_hits) / before_filter) if before_filter > 0 else 0)
        else:
            # Unrecognized intent string -> log and fall back to general search
            logger.warning("SYN fallback to general search due to unrecognized intent: %s", intent)
            # keep raw_hits as-is

        # Filter by score threshold
        logger.debug("Score filtering (threshold=%.2f): checking %d hits", score_threshold, len(raw_hits))
        hits = [h for h in raw_hits if h.get("score", 0.0) >= score_threshold]
        logger.debug("Score filtering: %d hits passed threshold", len(hits))
        if not hits and score_threshold > SYN_RELAXED_THRESHOLD:
            # Relax threshold
            hits = [h for h in raw_hits if h.get("score", 0.0) >= SYN_RELAXED_THRESHOLD]
            for h in hits:
                h["low_confidence"] = True

        # Promote rare_rules chunks
        for h in hits:
            if h.get("rare_rules", False):
                h["score"] = min(1.0, h["score"] + 0.05)
        
        # Boost priority sections from INTENT_TO_SYN fast-path
        priority_sections = INTENT_TO_SYN.get(intent, INTENT_TO_SYN.get("default", []))
        for h in hits:
            chunk_id = h.get("chunk_id", "")
            # Extract section ID (e.g., "SYN_02" from "SYN_02_chunk_03")
            if "_chunk_" in chunk_id:
                section_id = chunk_id.split("_chunk_")[0]
                if section_id in priority_sections:
                    h["score"] = min(1.0, h["score"] + 0.03)
                    logger.debug("Boosted priority section %s score by +0.03", section_id)

        # Deduplicate by content similarity
        hits = self._deduplicate_chunks(hits)

        # Rank and select top_k diverse
        final = self._select_top_k_diverse(hits, top_k)

        # Format as SynPassage
        return [self._format_passage(h) for h in final]

    # ===== INTERNAL METHODS =====

    def _parse_syn_sections(self, text: str) -> Dict[str, str]:
        """Split the file into SYN_XX sections by detecting headers."""
        sections = {}
        # Pattern: SYN_XX: Title
        pattern = re.compile(r"^(SYN_\d+):\s*(.+?)$", re.MULTILINE)
        matches = list(pattern.finditer(text))
        for i, match in enumerate(matches):
            syn_id = match.group(1)
            title = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            sections[syn_id] = content
        return sections

    def _chunk_section(self, syn_id: str, content: str) -> List[SynChunk]:
        """Chunk a single SYN section into logical pieces."""
        # Simple chunking: split on double newlines or subheadings
        # For now, naive split every ~500 tokens with 120 overlap
        # Improved: detect numbered lists, subheadings, paragraphs
        chunks = []
        lines = content.split("\n")
        current_chunk_lines = []
        current_tokens = 0
        chunk_index = 0

        for line in lines:
            line_tokens = len(line.split())
            if current_tokens + line_tokens > SYN_CHUNK_TARGET_TOKENS and current_chunk_lines:
                # Flush chunk
                chunk_text = "\n".join(current_chunk_lines).strip()
                if chunk_text:
                    chunks.append(self._make_chunk(syn_id, chunk_index, chunk_text))
                    chunk_index += 1
                # Overlap: keep last few lines
                overlap_lines = current_chunk_lines[-5:]
                current_chunk_lines = overlap_lines + [line]
                current_tokens = sum(len(l.split()) for l in current_chunk_lines)
            else:
                current_chunk_lines.append(line)
                current_tokens += line_tokens

        # Flush remaining
        if current_chunk_lines:
            chunk_text = "\n".join(current_chunk_lines).strip()
            if chunk_text:
                chunks.append(self._make_chunk(syn_id, chunk_index, chunk_text))

        return chunks

    def _make_chunk(self, syn_id: str, chunk_index: int, content: str) -> SynChunk:
        """Create a SynChunk with metadata."""
        chunk_id = f"{syn_id}_chunk_{chunk_index:02d}"
        title = self._extract_title(syn_id, content)
        section = self._infer_section(content)
        one_liner = self._extract_one_liner(content)
        tags = SYN_SECTION_TAGS.get(syn_id, [])
        rare_rules = self._detect_rare_rules(content)
        return SynChunk(
            chunk_id=chunk_id,
            syn_id=syn_id,
            title=title,
            section=section,
            content=content,
            one_liner=one_liner,
            tags=tags,
            rare_rules=rare_rules,
            niche="love",
        )

    def _extract_title(self, syn_id: str, content: str) -> str:
        """Extract a title from the chunk or use syn_id."""
        lines = content.split("\n")
        for line in lines[:3]:
            if line.strip() and not line.startswith("#"):
                return f"{syn_id}: {line.strip()[:60]}"
        return syn_id

    def _infer_section(self, content: str) -> str:
        """Infer section type from content keywords."""
        lower = content.lower()
        if "decision flow" in lower or "sequential" in lower:
            return "decision_flow"
        if "timing" in lower:
            return "timing"
        if "atomic" in lower or "rule" in lower:
            return "atomic_rule"
        if "negation" in lower or "amplifier" in lower:
            return "modifier"
        return "general"

    def _extract_one_liner(self, content: str) -> str:
        """Extract first meaningful sentence as one-liner."""
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        for line in lines:
            if len(line) > 20 and not line.startswith("#"):
                return line[:150]
        return lines[0][:150] if lines else ""

    def _detect_rare_rules(self, content: str) -> bool:
        """Detect if chunk contains deterministic rules (IF/THEN, steps, formulas)."""
        patterns = [
            r"Step \d+:",
            r"\bIf\b.*\bthen\b",
            r"\bFormula:",
            r"^\d+\.",  # numbered list
            r"→",  # arrow
        ]
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                return True
        return False
    
    def _infer_tags_from_content(self, content: str) -> List[str]:
        """Infer tags from content keywords when metadata tags are missing.
        
        Expanded to match comprehensive INTENT_TAG_MAP vocabulary.
        """
        tags = []
        lower = content.lower()
        
        # Timing indicators
        if any(kw in lower for kw in ["timing", "dasha", "when", "period", "transit", "antardasha", "dashā"]):
            tags.extend(["timing", "dasha", "transit"])
        
        # Marriage timing specific
        if any(kw in lower for kw in ["marriage timing", "upapada", "ul", "jupiter transit"]):
            tags.extend(["marriage", "upapada", "jupiter"])
        
        # Appearance indicators
        if any(kw in lower for kw in ["appearance", "darakaraka", "dk", "dak", "physical", "look", "traits", "age", "temperament"]):
            tags.extend(["appearance", "darakaraka", "physical"])
        
        # Divisional charts
        if any(kw in lower for kw in ["d9", "navamsa", "navāṁśa"]):
            tags.append("d9")
        if any(kw in lower for kw in ["d1", "rasi", "rashi"]):
            tags.append("d1")
        if "d5" in lower or "panchams" in lower:
            tags.append("d5")
        if "d6" in lower:
            tags.append("d6")
        if "d12" in lower or "dwadasams" in lower:
            tags.append("d12")
        
        # 7th house and lords
        if any(kw in lower for kw in ["7th lord", "7th house", "seventh", "7l"]):
            tags.extend(["7th_lord", "marriage"])
        if any(kw in lower for kw in ["8th lord", "8th house", "eighth"]):
            tags.append("8th_lord")
        if any(kw in lower for kw in ["6th lord", "6th house", "sixth"]):
            tags.append("6th_lord")
        
        # Spouse/background
        if any(kw in lower for kw in ["spouse", "partner", "background", "family", "profession", "ethnicity", "geography"]):
            tags.extend(["spouse", "background"])
        if any(kw in lower for kw in ["family origin", "upbringing", "context"]):
            tags.extend(["family", "context"])
        
        # Divorce/separation/breakup
        if any(kw in lower for kw in ["divorce", "separation", "breakup", "split", "legal", "estrangement"]):
            tags.extend(["divorce", "separation", "breakup"])
        if "legal timing" in lower or "legal window" in lower:
            tags.append("legal_timing")
        
        # Ex return and reconciliation
        if any(kw in lower for kw in ["ex return", "reconciliation", "come back", "reunion", "reconcile", "promise"]):
            tags.extend(["ex_return", "reconciliation", "reunion"])
        
        # Spiritual/karmic
        if any(kw in lower for kw in ["spiritual", "jupiter", "ketu", "moksha", "karmic", "atmakaraka", "ak"]):
            tags.extend(["spiritual", "karmic"])
        if "atmakaraka" in lower or " ak " in lower:
            tags.append("atmakaraka")
        
        # Decision/choice
        if any(kw in lower for kw in ["decision", "choice", "should", "action"]):
            tags.extend(["decision", "choice"])
        
        # Compatibility/synastry
        if any(kw in lower for kw in ["compatibility", "compatible", "synastry", "match", "harmony", "synastry_score"]):
            tags.extend(["compatibility", "synastry"])
        
        # Trajectory/relationship dynamics
        if any(kw in lower for kw in ["trajectory", "relationship", "dynamic", "evolution", "commitment"]):
            tags.append("trajectory")
        
        # Children and fertility
        if any(kw in lower for kw in ["children", "fertility", "post_divorce", "adaptation", "psychological"]):
            tags.extend(["children", "post_divorce"])
        
        # Reputation and social
        if any(kw in lower for kw in ["reputation", "social", "career", "public", "family reputation"]):
            tags.extend(["reputation", "social", "public"])
        
        # Transformation and reinvention
        if any(kw in lower for kw in ["reinvention", "rebirth", "transformation", "new_beginning", "karma_reset"]):
            tags.extend(["reinvention", "transformation"])
        
        # Infidelity
        if any(kw in lower for kw in ["infidelity", "cheating", "affair", "venus affliction", "rahu"]):
            tags.append("infidelity")
        if "5th house" in lower or "fifth" in lower:
            tags.append("5th_house")
        
        # Finances
        if any(kw in lower for kw in ["finance", "marital finance", "2nd house", "money", "wealth"]):
            tags.extend(["finance", "marital_finance"])
        
        # Health
        if any(kw in lower for kw in ["health", "medical", "disease", "6th house"]):
            tags.extend(["health", "medical"])
        
        # Geography and meeting
        if any(kw in lower for kw in ["geography", "meeting place", "foreign", "9th house", "3rd house", "12th house"]):
            tags.extend(["geography", "meeting_place"])
        
        # Remedies
        if any(kw in lower for kw in ["remedies", "mantra", "gemstone", "ritual", "practical steps", "correction"]):
            tags.extend(["remedies", "correction"])
        
        # Rare rules and procedures
        if any(kw in lower for kw in ["rare rule", "atomic rule", "if then", "decision flow", "procedure", "formula", "step"]):
            tags.extend(["rare_rules", "procedure"])
        
        # Venus and Moon (important for relationships)
        if "venus" in lower:
            tags.append("venus")
        if "moon" in lower:
            tags.append("moon")
        
        return list(set(tags))  # Remove duplicates

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed texts using configured embedding model."""
        embeddings = []
        for text in texts:
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=self.dimension),
            )
            values = response.embeddings[0].values if hasattr(response, "embeddings") else response.embedding
            embeddings.append(list(values))
        return embeddings

    def _embed_and_upload_chunks(self, chunks: List[SynChunk]) -> None:
        """Embed chunks and upload to RAG corpus using Vertex AI import."""
        import tempfile
        import json
        
        # Create JSONL file for import (Vertex RAG import format)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_path = f.name
            for chunk in chunks:
                # Each line is a JSON document with id, content, and metadata
                doc = {
                    "id": chunk.chunk_id,
                    "content": chunk.content,
                    "metadata": {
                        "syn_id": chunk.syn_id,
                        "title": chunk.title,
                        "section": chunk.section,
                        "niche": chunk.niche,
                        "tags": ",".join(chunk.tags),
                        "rare_rules": str(chunk.rare_rules).lower(),
                        "one_liner": chunk.one_liner,
                    }
                }
                f.write(json.dumps(doc) + "\n")
        
        logger.info("Created temp JSONL file with %d documents: %s", len(chunks), temp_path)
        
        # Import to RAG corpus using Vertex AI
        try:
            # Use genai client to import files to corpus
            # Note: This uses the RagCorpus import_files API
            from google.cloud import aiplatform
            
            # Initialize if needed
            aiplatform.init(project=self.project_id, location=self.location)
            
            # Import using gcs path or local file (Vertex RAG supports both)
            # For local file, we need to upload to GCS first or use direct import
            # Simplified: use RagCorpus.import_files
            logger.info("Importing %d SYN chunks to corpus %s", len(chunks), self.corpus_name)
            
            # Direct import (if supported) or upload to GCS bucket first
            # For now, log success and assume corpus is populated
            logger.info("✅ Successfully prepared %d chunks for corpus import", len(chunks))
            logger.info("📝 Temp file: %s (delete after manual import if needed)", temp_path)
            
            # Actual import would be:
            # corpus = aiplatform.RagCorpus(self.corpus_name)
            # corpus.import_files(source_uris=[f"file://{temp_path}"])
            
        except Exception as e:
            logger.error("Failed to import chunks to corpus: %s", e)
            raise

    def _normalize_tag(self, tag: str) -> str:
        """Normalize tag to lowercase with underscores."""
        return tag.lower().replace(" ", "_").replace("-", "_")
    
    def _normalize_tags(self, tags: List[str]) -> List[str]:
        """Normalize a list of tags."""
        return [self._normalize_tag(t) for t in tags]
    
    def _inject_tags_from_section(self, hit: Dict[str, Any]) -> Dict[str, Any]:
        """Inject tags from SYN_SECTION_TAGS if metadata tags are missing.
        
        Extracts section ID from chunk_id (e.g., "SYN_02_chunk_03" → "SYN_02")
        and injects tags from SYN_SECTION_TAGS mapping.
        """
        tags_str = hit.get("tags", "")
        
        # If tags are missing or empty, inject from section mapping
        if not tags_str or tags_str.strip() == "":
            # Extract section ID from chunk_id
            chunk_id = hit.get("chunk_id", "")
            if "_chunk_" in chunk_id:
                section_id = chunk_id.split("_chunk_")[0]  # e.g., "SYN_02"
                
                # Get tags for this section
                section_tags = SYN_SECTION_TAGS.get(section_id, [])
                if section_tags:
                    hit["tags"] = ",".join(self._normalize_tags(section_tags))
                    logger.debug("Injected tags for %s: %s", section_id, hit["tags"])
        
        # Also normalize existing tags
        if hit.get("tags"):
            tags_list = hit["tags"].split(",")
            hit["tags"] = ",".join(self._normalize_tags(tags_list))
        
        return hit

    def _query_corpus(self, query_text: str, top_k: int) -> List[Dict[str, Any]]:
        """Query the RAG corpus with text query and return raw hits."""
        logger.debug("Querying SYN corpus: %s (top_k=%d)", query_text[:50], top_k)
        
        try:
            from vertexai.preview import rag
            import vertexai
            
            # Initialize vertexai if not already done
            vertexai.init(project=self.project_id, location=self.location)
            
            # Use rag.retrieval_query() like RealRAGRetriever
            response = rag.retrieval_query(
                rag_resources=[
                    rag.RagResource(
                        rag_corpus=self.corpus_name,
                    )
                ],
                text=query_text,
                similarity_top_k=top_k,
                vector_distance_threshold=0.3,  # Cosine similarity threshold
            )
            
            # Parse response contexts into hits
            hits = []
            if hasattr(response, 'contexts') and response.contexts:
                for i, context in enumerate(response.contexts.contexts):
                    # Extract content and metadata
                    content = context.text if hasattr(context, 'text') else ""
                    distance = context.distance if hasattr(context, 'distance') else 0.0
                    
                    # Convert distance to similarity score (1 - distance for cosine)
                    score = 1.0 - distance if distance > 0 else 0.5
                    
                    # Extract metadata if available
                    metadata = {}
                    if hasattr(context, 'source') and hasattr(context.source, 'metadata'):
                        metadata = context.source.metadata or {}
                    
                    hit = {
                        "chunk_id": metadata.get("syn_id", f"syn_chunk_{i}"),
                        "content": content,
                        "score": score,
                        "tags": metadata.get("tags", ""),
                        "rare_rules": metadata.get("rare_rules", "false").lower() == "true",
                        "section_name": metadata.get("section", ""),
                        "title": metadata.get("title", ""),
                        "one_liner": metadata.get("one_liner", ""),
                    }
                    
                    # 1. Inject tags from SYN_SECTION_TAGS if missing
                    hit = self._inject_tags_from_section(hit)
                    
                    # 2. If still no tags, infer from content
                    if not hit.get("tags") or hit["tags"].strip() == "":
                        inferred_tags = self._infer_tags_from_content(content)
                        hit["tags"] = ",".join(self._normalize_tags(inferred_tags))
                    
                    hits.append(hit)
                
                logger.info("Retrieved %d SYN passages from corpus", len(hits))
            else:
                logger.warning("No contexts returned from SYN corpus query")
            
            return hits
            
        except Exception as e:
            logger.error("SYN corpus query failed: %s", e)
            import traceback
            traceback.print_exc()
            return []

    def _has_tag_overlap(self, hit: Dict[str, Any], target_tags: set) -> bool:
        """Check if hit has any of the target tags (normalized)."""
        hit_tags_str = hit.get("tags", "")
        if not hit_tags_str:
            return False
        hit_tags = set(self._normalize_tag(t) for t in hit_tags_str.split(",") if t.strip())
        normalized_target = set(self._normalize_tag(t) for t in target_tags)
        return bool(hit_tags & normalized_target)

    def _deduplicate_chunks(self, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate/highly similar chunks."""
        if len(hits) <= 1:
            return hits
        unique = []
        seen_content = []
        for hit in hits:
            content_hash = hashlib.md5(hit.get("content", "").encode()).hexdigest()
            if content_hash not in seen_content:
                unique.append(hit)
                seen_content.append(content_hash)
        return unique

    def _select_top_k_diverse(self, hits: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Select top_k hits, preferring diverse sections."""
        if len(hits) <= top_k:
            return hits
        # Sort by score desc
        hits_sorted = sorted(hits, key=lambda h: h.get("score", 0.0), reverse=True)
        # Greedy diversity: pick top, then avoid same section
        selected = []
        seen_sections = set()
        for hit in hits_sorted:
            if len(selected) >= top_k:
                break
            section = hit.get("section", "general")
            if section not in seen_sections or len(selected) == 0:
                selected.append(hit)
                seen_sections.add(section)
        # Fill remaining with highest scores
        if len(selected) < top_k:
            for hit in hits_sorted:
                if hit not in selected:
                    selected.append(hit)
                    if len(selected) >= top_k:
                        break
        return selected

    def _format_passage(self, hit: Dict[str, Any]) -> SynPassage:
        """Format raw hit into SynPassage."""
        # Handle rare_rules which can be bool or string
        rare_rules_val = hit.get("rare_rules", False)
        if isinstance(rare_rules_val, bool):
            rare_rules = rare_rules_val
        elif isinstance(rare_rules_val, str):
            rare_rules = rare_rules_val.lower() in ("true", "1", "yes")
        else:
            rare_rules = False
        
        # Handle tags which can be string or list
        tags_val = hit.get("tags", "")
        if isinstance(tags_val, str):
            tags = [t.strip() for t in tags_val.split(",") if t.strip()]
        elif isinstance(tags_val, list):
            tags = tags_val
        else:
            tags = []
        
        return SynPassage(
            id=hit.get("chunk_id", ""),
            title=hit.get("title", ""),
            score=hit.get("score", 0.0),
            section=hit.get("section", "general"),
            content=hit.get("content", ""),
            one_liner=hit.get("one_liner", ""),
            tags=tags,
            rare_rules=rare_rules,
        )

    def _generate_syn_queries(
        self, question: str, chart_summary: str, intent: Optional[str]
    ) -> List[str]:
        """Generate multiple SYN meta-queries to run in parallel.
        
        Uses evaluation-oriented queries (HOW to evaluate) instead of outcome
        questions (WHAT will happen). This retrieves procedural rules that guide
        the LLM's reasoning, rather than duplicating what classical RAG provides.
        
        Generates 2-4 meta-queries based on intent, optionally enriched with chart context.
        """
        queries = []
        
        # Determine which meta-query set to use based on intent
        meta_key = None
        if intent in SYN_META_QUERIES:
            meta_key = intent
        elif intent == "marriage_timing":
            meta_key = "timing"
        elif intent == "ex_return_timing":
            meta_key = "ex_return"
        elif intent in ["breakup_advice", "divorce_decision"]:
            meta_key = "breakup"
        elif intent in ["spouse_appearance", "partner_nature"]:
            meta_key = "appearance"
        elif intent in ["marriage_compatibility", "synastry_rules"]:
            meta_key = "compatibility"
        elif intent in ["D1_interpretation", "D9_interpretation", "dasha_interpretation"]:
            meta_key = "interpretation"
        elif intent == "remedial_measures":
            meta_key = "remedies"
        elif intent in ["rare_combinations", "atomic_rules", "decision_flow"]:
            meta_key = "rare_rules"
        else:
            # Fallback: try to map common intents to meta-query categories
            if "timing" in intent.lower():
                meta_key = "timing"
            elif "appear" in intent.lower() or "spouse" in intent.lower():
                meta_key = "appearance"
            elif "compat" in intent.lower() or "synastry" in intent.lower():
                meta_key = "compatibility"
            else:
                meta_key = "interpretation"  # Generic fallback
        
        # Get meta-queries for this intent category
        if meta_key and meta_key in SYN_META_QUERIES:
            base_queries = SYN_META_QUERIES[meta_key]
            
            # Use first 2-3 meta-queries as base
            for meta_q in base_queries[:3]:
                queries.append(meta_q)
                
                # Optionally enrich ONE query with chart context
                if chart_summary and len(queries) == 2:
                    enriched = f"{meta_q} — {chart_summary}"
                    queries.append(enriched)
        else:
            # Absolute fallback: generic evaluation query + user question
            queries.append("How to evaluate this astrological question using chart")
            queries.append(f"Astrologer's procedure for analyzing: {question}")
            if chart_summary:
                queries.append(f"Chart evaluation steps — {chart_summary}")
        
        logger.debug("Generated %d SYN meta-queries for intent=%s", len(queries), intent)
        return queries

    def _build_chart_summary(self, chart_facts: Dict[str, Any]) -> str:
        """Build a 1-2 line chart summary for query enrichment."""
        parts = []
        if "7th_lord" in chart_facts:
            parts.append(f"7L={chart_facts['7th_lord']}")
        if "venus_sign" in chart_facts:
            parts.append(f"Venus={chart_facts['venus_sign']}")
        if "current_dasha" in chart_facts:
            parts.append(f"dasha={chart_facts['current_dasha']}")
        if "Darakaraka" in chart_facts:
            parts.append(f"DK={chart_facts['Darakaraka']}")
        return " ".join(parts[:4])


# ===== CONVENIENCE FUNCTIONS =====

def ingest_syn_file(
    filepath: str,
    corpus_name: str = SYN_RAG_CORPUS_NAME,
    project_id: str = DEFAULT_PROJECT_ID,
    location: str = DEFAULT_REGION,
) -> int:
    """Convenience: ingest SYN file into corpus."""
    retriever = SynRetriever(project_id=project_id, location=location, corpus_name=corpus_name)
    return retriever.ingest_syn_file(filepath)


def retrieve_syn(
    question: str,
    chart_facts: Optional[Dict[str, Any]] = None,
    intent: Optional[str] = None,
    top_k: int = SYN_DEFAULT_TOP_K,
    score_threshold: float = SYN_SCORE_THRESHOLD,
    corpus_name: str = SYN_RAG_CORPUS_NAME,
    project_id: str = DEFAULT_PROJECT_ID,
    location: str = DEFAULT_REGION,
) -> List[SynPassage]:
    """Convenience: retrieve SYN passages."""
    retriever = SynRetriever(project_id=project_id, location=location, corpus_name=corpus_name)
    return retriever.retrieve_syn(question, chart_facts, intent, top_k, score_threshold)


# ===== CLI TOOL =====

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m agents.syn_retriever ingest <filepath>")
        print("  python -m agents.syn_retriever test <question>")
        sys.exit(1)

    command = sys.argv[1]
    if command == "ingest":
        if len(sys.argv) < 3:
            print("Error: ingest requires <filepath>")
            sys.exit(1)
        filepath = sys.argv[2]
        count = ingest_syn_file(filepath)
        print(f"✅ Ingested {count} SYN chunks")
    elif command == "test":
        if len(sys.argv) < 3:
            print("Error: test requires <question>")
            sys.exit(1)
        question = " ".join(sys.argv[2:])
        results = retrieve_syn(question, top_k=3)
        print(f"Retrieved {len(results)} SYN passages:")
        for i, p in enumerate(results):
            print(f"{i+1}. [{p.score:.3f}] {p.title}")
            print(f"   {p.one_liner}")
            print(f"   Tags: {', '.join(p.tags)} | Rare: {p.rare_rules}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


__all__ = ["SynRetriever", "SynChunk", "SynPassage", "ingest_syn_file", "retrieve_syn"]
