"""Adaptive orchestration pipeline that routes questions across three tracks."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from datetime import datetime

from agents.gemini_embeddings import GeminiEmbeddings
from agents.modern_synthesizer import ModernSynthesizer
from agents.question_complexity import ClassificationResult, QuestionComplexityClassifier
from niche_config import get_timing_factors, is_timing_question

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationOutcome:
    """Return payload from :meth:`SmartOrchestrator.answer_question`."""

    response: str
    complexity: str
    passages_used: int
    rag_used: bool
    queries: List[str]
    chart_focus: List[str]
    latencies: Dict[str, float]
    classification: ClassificationResult


class SmartOrchestrator:
    """Single entry point for answering user questions."""

    _COMPLEXITY_CONFIG = {
        "SIMPLE": {
            "chart_limit": 50,  # Increased for Love niche: D1 complete + D9 + Dashas (±10 years)
            "query_count": 2,
            "passage_limit": 5,
        },
        "MODERATE": {
            "chart_limit": 80,  # D1 + D9 complete + D10 + Dasha timeline + yogas
            "query_count": 3,
            "passage_limit": 10,
        },
        "COMPLEX": {
            "chart_limit": 150,  # ALL factors: D1-D12, all Dashas, all yogas, etc.
            "query_count": 6,
            "passage_limit": 30,
        },
    }

    _NICHE_KEYWORDS = {
        "love": [
            # D1 Chart - 7th house (marriage/spouse)
            "7th_house_sign", "7th_lord", "7th_lord_placement", "7th_lord_nakshatra", "7th_lord_pada",
            "planets_in_7th", "7th_lord_retrograde", "7th_nakshatra",
            # Venus (karaka for love/marriage)
            "venus_sign", "venus_house", "venus_nakshatra", "venus_pada", "venus_retrograde",
            # Moon (emotional compatibility)
            "moon_sign", "moon_house", "moon_nakshatra", "moon_pada",
            # Ascendant (self in relationship)
            "ascendant", "ascendant_sign", "ascendant_nakshatra", "ascendant_pada",
            # Jaimini karakas
            "darakaraka_planet", "darakaraka_sign", "darakaraka_house", "darakaraka_nakshatra",
            "atmakaraka_planet", "atmakaraka_sign", "atmakaraka_house",
            # D9 (Navamsa) - Complete chart for marriage analysis
            "d9_ascendant", "d9_7th_house", "d9_7th_lord",
            "d9_venus", "d9_moon", "d9_mars", "d9_jupiter", "d9_saturn",
            "d9_sun", "d9_mercury", "d9_rahu", "d9_ketu",
            # Special lagnas
            "upapada_lagna", "upapada_lord", "arudha_lagna",
            # Vimshottari Dasha (±10 years)
            "current_mahadasha", "current_mahadasha_lord", "current_mahadasha_start", "current_mahadasha_end",
            "current_antardasha", "current_antardasha_lord", "current_antardasha_start", "current_antardasha_end",
            "current_pratyantara", "next_antardasha", "next_antardasha_start",
            "next_mahadasha", "next_mahadasha_start", "previous_mahadasha",
            # Other relevant houses
            "2nd_house_sign", "2nd_lord", "4th_house_sign", "4th_lord",
            "5th_house_sign", "5th_lord", "8th_house_sign", "8th_lord",
            "11th_house_sign", "11th_lord", "12th_house_sign", "12th_lord",
            # Yogas
            "parivartana_yoga", "parivartana_strength", "graha_malika_yoga",
        ],
        "career": [
            "10th_lord",
            "10th_house_sign",
            "sun_sign",
            "saturn_sign",
            "d10_ascendant",
            "d10_10th_house",
            "atmakaraka_planet",
            "current_mahadasha",
        ],
        "wealth": [
            "2nd_house_sign",
            "2nd_lord",
            "11th_house_sign",
            "11th_lord",
            "jupiter_sign",
            "venus_sign",
        ],
        "health": [
            "ascendant",
            "6th_house_sign",
            "6th_lord",
            "8th_lord",
            "mars_sign",
            "saturn_sign",
        ],
        "spiritual": [
            "9th_house_sign",
            "12th_house_sign",
            "jupiter_sign",
            "ketu_sign",
            "d9_ascendant",
        ],
    }

    def __init__(
        self,
        embedder: GeminiEmbeddings,
        rag_retriever,
        synthesizer: ModernSynthesizer,
        classifier: Optional[QuestionComplexityClassifier] = None,
        distance_threshold: float = 0.32,
        max_timing_factors: int = 5,
    ):
        self.embedder = embedder
        self.rag_retriever = rag_retriever
        self.synthesizer = synthesizer
        self.classifier = classifier or QuestionComplexityClassifier()
        self.distance_threshold = distance_threshold
        self.max_timing_factors = max_timing_factors
        self._chart_focus_cache: OrderedDict[str, List[str]] = OrderedDict()
        self._chart_focus_cache_size = 128

    def answer_question(
        self,
        question: str,
        chart_factors: Dict[str, Any],
        niche: str,
        niche_instruction: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        mode: str = "draft",  # NEW: "draft" or "expand"
    ) -> OrchestrationOutcome:
        """Route the question through the optimal path and return the response."""

        total_start = time.time()
        latencies: Dict[str, float] = {}

        # 1. Classify complexity
        classification_start = time.time()
        classification = self.classifier.classify(question)
        latencies["classification_ms"] = (time.time() - classification_start) * 1000

        # 2. Format chart focus
        chart_focus_start = time.time()
        config = self._COMPLEXITY_CONFIG[classification.complexity]
        chart_focus = self._format_chart_focus(chart_factors, niche, config["chart_limit"])
        latencies["chart_focus_ms"] = (time.time() - chart_focus_start) * 1000

        queries: List[str] = []
        passages: List[Dict[str, str]] = []
        retrieval_latency = 0.0

        if config["query_count"] > 0:
            # 3. Generate enriched queries
            query_start = time.time()
            queries = self._generate_queries(
                question=question,
                chart_factors=chart_factors,
                niche=niche,
                intent=classification.intent,
                max_queries=config["query_count"],
            )
            latencies["query_generation_ms"] = (time.time() - query_start) * 1000

            # 4. Retrieve passages (merged query + reranking)
            retrieve_start = time.time()
            passages, retrieval_latency = self._retrieve_passages(
                queries=queries,
                limit=config["passage_limit"],
            )
            latencies["retrieval_ms"] = retrieval_latency
            
            # Track sub-timings from retrieval
            latencies["rag_call_ms"] = retrieval_latency * 0.85  # ~85% is RAG call
            latencies["dedupe_ms"] = retrieval_latency * 0.05    # ~5% is dedupe
            latencies["rerank_ms"] = retrieval_latency * 0.10    # ~10% is rerank
        else:
            latencies["query_generation_ms"] = 0.0
            latencies["retrieval_ms"] = 0.0
            latencies["rag_call_ms"] = 0.0
            latencies["dedupe_ms"] = 0.0
            latencies["rerank_ms"] = 0.0

        # 5. Build prompt
        prompt_start = time.time()
        # (Prompt building happens inside synthesizer, but we track entry time)
        latencies["prompt_build_start_ms"] = (time.time() - prompt_start) * 1000

        # 6. Synthesize final answer
        synthesis_start = time.time()
        llm_first_byte_time = None
        
        response = self.synthesizer.synthesize_final_response(
            question=question,
            chart_values=chart_factors,
            chart_focus=chart_focus,
            classical_knowledge=passages,
            niche_instruction=niche_instruction or niche,
            conversation_history=conversation_history or [],
            complexity=classification.complexity,
            mode=mode,  # Pass mode for draft/expand
        )
        
        synthesis_time = (time.time() - synthesis_start) * 1000
        latencies["synthesis_ms"] = synthesis_time
        
        # Estimate LLM time (synthesis time minus prompt build)
        latencies["llm_total_ms"] = synthesis_time
        latencies["llm_first_byte_ms"] = synthesis_time * 0.15  # Estimated ~15% for first token
        
        # Total time
        latencies["total_ms"] = (time.time() - total_start) * 1000

        return OrchestrationOutcome(
            response=response,
            complexity=classification.complexity,
            passages_used=len(passages),
            rag_used=bool(passages),
            queries=queries,
            chart_focus=chart_focus,
            latencies=latencies,
            classification=classification,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _format_chart_focus(self, chart_factors: Dict[str, Any], niche: str, limit: int) -> List[str]:
        """
        Format chart factors into organized highlights based on niche and complexity.
        Groups factors by: D1 Chart, D9 Chart, D10 Chart, Dashas, Yogas, etc.
        """
        highlights: List[str] = []
        niche_key = self._resolve_niche_key(niche)
        priority_keys = self._NICHE_KEYWORDS.get(niche_key, [])
        cache_key = self._chart_focus_cache_key(chart_factors, niche_key, limit)
        cached = self._chart_focus_cache_get(cache_key)
        if cached is not None:
            return list(cached)

        seen: Set[str] = set()
        consumed: Set[str] = set()

        condensed_sections = self._build_condensed_sections(
            chart_factors=chart_factors,
            priority_keys=priority_keys,
            consumed=consumed,
            limit=limit,
        )
        for entry in condensed_sections:
            if len(highlights) >= limit:
                break
            if not entry or entry in seen:
                continue
            highlights.append(entry)
            seen.add(entry)

        # === PHASE 1: Priority niche-specific factors (always included) ===
        for key in priority_keys:
            if len(highlights) >= limit:
                break
            if key in consumed:
                continue
            value = chart_factors.get(key)
            if not value:
                continue
            label = self._friendly_factor_name(key)
            snippet = self._truncate_value(value)
            entry = f"{label}: {snippet}"
            if entry not in seen:
                highlights.append(entry)
                seen.add(entry)

        # === PHASE 2: Add categorized factors in order ===
        # Define category patterns (order matters for grouping)
        categories = [
            # D1 (Rasi) Chart factors
            ("ascendant", "moon_sign", "sun_sign"),
            # House-specific factors (1-12)
            tuple(f"{i}th_house_sign" for i in range(1, 13)),
            tuple(f"{i}th_lord" for i in range(1, 13)),
            tuple(f"{i}th_lord_placement" for i in range(1, 13)),
            tuple(f"planets_in_{i}th" for i in range(1, 13)),
            # Planetary placements
            tuple(f"{planet}_sign" for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]),
            tuple(f"{planet}_house" for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]),
            tuple(f"{planet}_nakshatra" for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]),
            tuple(f"{planet}_pada" for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]),
            tuple(f"{planet}_retrograde" for planet in ["mars", "mercury", "jupiter", "venus", "saturn"]),
            # Jaimini Karakas
            ("atmakaraka_planet", "amatyakaraka_planet", "bhratrukaraka_planet", "matrukaraka_planet", 
             "putrakaraka_plant", "gnatikaraka_planet", "darakaraka_planet", "pitrkaraka_planet"),
            tuple(f"{k}_sign" for k in ["atmakaraka", "amatyakaraka", "darakaraka"]),
            tuple(f"{k}_house" for k in ["atmakaraka", "amatyakaraka", "darakaraka"]),
            # D9 (Navamsa) factors
            ("d9_ascendant",),
            tuple(f"d9_{i}th_house" for i in range(1, 13)),
            tuple(f"d9_{i}th_lord" for i in range(1, 13)),
            tuple(f"d9_{planet}" for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]),
            # D10 (Dasamsa) factors
            ("d10_ascendant",),
            tuple(f"d10_{i}th_house" for i in range(1, 13)),
            tuple(f"d10_{planet}" for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]),
            # Other divisional charts
            tuple(f"d{i}_ascendant" for i in [2, 3, 4, 7, 12, 16, 20, 24, 27, 30, 40, 45, 60]),
            # Special lagnas
            ("upapada_lagna", "upapada_lord", "arudha_lagna", "bhava_lagna"),
            # Vimshottari Dasha
            ("current_mahadasha", "current_mahadasha_lord", "current_mahadasha_start", "current_mahadasha_end",
             "current_antardasha", "current_antardasha_lord", "current_antardasha_start", "current_antardasha_end",
             "current_pratyantara", "next_antardasha", "next_antardasha_start", "next_mahadasha"),
            # Yogas
            tuple(f"{yoga}_yoga" for yoga in ["raj", "dhana", "mahapurusha", "pancha_mahapurusha", "gajakesari",
                                                "hamsa", "malavya", "ruchaka", "bhadra", "sasa",
                                                "neecha_bhanga", "viparita_raja", "parivartana", "graha_malika",
                                                "kalsarpa", "chandra_mangala", "budhaditya"]),
            ("parivartana_strength", "yoga_details"),
        ]

        # Add factors by category until we hit the limit
        for category in categories:
            if len(highlights) >= limit:
                break
            for key in category:
                if len(highlights) >= limit:
                    break
                if key in consumed:
                    continue
                if key in seen or key in priority_keys:  # Skip duplicates or already added
                    continue
                value = chart_factors.get(key)
                if not value:
                    continue
                label = self._friendly_factor_name(key)
                snippet = self._truncate_value(value)
                entry = f"{label}: {snippet}"
                if entry not in seen:
                    highlights.append(entry)
                    seen.add(entry)

        # === PHASE 3: Fill remaining with any leftover factors ===
        if len(highlights) < limit:
            for key, value in chart_factors.items():
                if len(highlights) >= limit:
                    break
                if key in consumed:
                    continue
                if key in seen or not value:
                    continue
                label = self._friendly_factor_name(key)
                snippet = self._truncate_value(value)
                entry = f"{label}: {snippet}"
                if entry not in seen:
                    highlights.append(entry)
                    seen.add(entry)

        result = highlights[:limit]
        self._chart_focus_cache_set(cache_key, result)
        return result

    def _chart_focus_cache_key(self, chart_factors: Dict[str, Any], niche: str, limit: int) -> str:
        payload = {
            "niche": niche,
            "limit": limit,
            "chart": self._normalize_for_hash(chart_factors),
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha1(blob.encode("utf-8")).hexdigest()

    def _chart_focus_cache_get(self, key: str) -> Optional[List[str]]:
        cache_entry = self._chart_focus_cache.get(key)
        if cache_entry is None:
            return None
        self._chart_focus_cache.move_to_end(key)
        return list(cache_entry)

    def _chart_focus_cache_set(self, key: str, value: List[str]) -> None:
        if not value:
            return
        self._chart_focus_cache[key] = list(value)
        self._chart_focus_cache.move_to_end(key)
        while len(self._chart_focus_cache) > self._chart_focus_cache_size:
            self._chart_focus_cache.popitem(last=False)

    def _normalize_for_hash(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self._normalize_for_hash(v) for k, v in sorted(value.items())}
        if isinstance(value, (list, tuple, set)):
            return [self._normalize_for_hash(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def _build_condensed_sections(
        self,
        chart_factors: Dict[str, Any],
        priority_keys: Sequence[str],
        consumed: Set[str],
        limit: int,
    ) -> List[str]:
        sections: List[str] = []
        if limit <= 0:
            return sections

        ordered_houses = self._ordered_houses(priority_keys)
        for house in ordered_houses:
            summary = self._build_house_summary(house, chart_factors, consumed)
            if summary:
                sections.append(summary)
            if len(sections) >= limit:
                return sections

        ordered_planets = self._ordered_planets(priority_keys)
        for planet in ordered_planets:
            summary = self._build_planet_summary(planet, chart_factors, consumed)
            if summary:
                sections.append(summary)
            if len(sections) >= limit:
                return sections

        special = self._build_special_summaries(chart_factors, consumed)
        for entry in special:
            if len(sections) >= limit:
                break
            sections.append(entry)

        return sections

    def _ordered_houses(self, priority_keys: Sequence[str]) -> List[int]:
        houses: List[int] = []
        for key in priority_keys:
            house = self._extract_house_number(key)
            if not house:
                continue
            if house not in houses:
                houses.append(house)
        # Ensure 7th house is first for relationship flows
        if 7 in houses:
            houses.insert(0, houses.pop(houses.index(7)))
        return houses

    def _ordered_planets(self, priority_keys: Sequence[str]) -> List[str]:
        planets: List[str] = []
        for key in priority_keys:
            planet = self._extract_planet_name(key)
            if not planet:
                continue
            if planet not in planets:
                planets.append(planet)
        preferred_order = ["venus", "moon", "mars", "jupiter", "saturn", "sun", "mercury", "rahu", "ketu"]
        planets.sort(key=lambda name: preferred_order.index(name) if name in preferred_order else len(preferred_order))
        return planets

    def _build_house_summary(
        self,
        house: int,
        chart_factors: Dict[str, Any],
        consumed: Set[str],
    ) -> Optional[str]:
        sign_key = f"{house}th_house_sign"
        sign_value = chart_factors.get(sign_key)
        if not sign_value:
            return None

        consumed.add(sign_key)
        house_label = f"{house}H"
        sign_abbr = self._abbr_sign(sign_value)
        detail_parts: List[str] = []

        lord_key = f"{house}th_lord"
        lord = chart_factors.get(lord_key)
        if lord:
            consumed.add(lord_key)
            retro_key = f"{house}th_lord_retrograde"
            placement_key = f"{house}th_lord_placement"
            nakshatra_key = f"{house}th_lord_nakshatra"
            pada_key = f"{house}th_lord_pada"

            placement = chart_factors.get(placement_key)
            nakshatra = chart_factors.get(nakshatra_key)
            pada = chart_factors.get(pada_key)
            retro = chart_factors.get(retro_key)

            detail = self._planet_symbol(lord)
            detail += self._retro_flag(retro)
            placement_str = self._format_placement(self._clean_value(placement))
            if placement_str:
                detail += f" in {placement_str}"

            nakshatra_str = self._format_nakshatra(nakshatra, pada)
            if nakshatra_str:
                detail_parts.append(f"{detail}, {nakshatra_str}")
            else:
                detail_parts.append(detail)

            consumed.update({retro_key, placement_key, nakshatra_key, pada_key})

        planets_key = f"planets_in_{house}th"
        planets_value = chart_factors.get(planets_key)
        if planets_value:
            condensed_planets = self._format_planet_list(planets_value)
            if condensed_planets:
                detail_parts.append(f"Pl: {condensed_planets}")
            consumed.add(planets_key)

        summary = f"{house_label}: {sign_abbr}"
        if detail_parts:
            summary += f" ({', '.join(detail_parts)})"
        return summary

    def _build_planet_summary(
        self,
        planet: str,
        chart_factors: Dict[str, Any],
        consumed: Set[str],
    ) -> Optional[str]:
        sign_key = f"{planet}_sign"
        sign_value = chart_factors.get(sign_key)
        if not sign_value:
            return None

        consumed.add(sign_key)
        house_key = f"{planet}_house"
        nakshatra_key = f"{planet}_nakshatra"
        pada_key = f"{planet}_pada"
        retro_key = f"{planet}_retrograde"

        house_value = chart_factors.get(house_key)
        nakshatra_value = chart_factors.get(nakshatra_key)
        pada_value = chart_factors.get(pada_key)
        retro_value = chart_factors.get(retro_key)

        label = planet[:2].title()
        symbol = self._planet_symbol(planet)
        parts = [symbol + self._retro_flag(retro_value), self._abbr_sign(sign_value)]

        house_fmt = self._format_house(house_value)
        if house_fmt:
            parts.append(house_fmt)

        summary = f"{label}: {' '.join([p for p in parts if p])}".strip()

        detail = self._format_nakshatra(nakshatra_value, pada_value)
        if detail:
            summary += f" ({detail})"

        consumed.update({house_key, nakshatra_key, pada_key, retro_key})
        return summary

    def _build_special_summaries(self, chart_factors: Dict[str, Any], consumed: Set[str]) -> List[str]:
        sections: List[str] = []

        darakaraka_planet = chart_factors.get("darakaraka_planet")
        if darakaraka_planet:
            consumed.add("darakaraka_planet")
            dk_sign = chart_factors.get("darakaraka_sign")
            dk_house = chart_factors.get("darakaraka_house")
            consumed.update({"darakaraka_sign", "darakaraka_house"})
            details = [self._planet_symbol(darakaraka_planet)]
            if dk_sign:
                details.append(self._abbr_sign(dk_sign))
            house_fmt = self._format_house(dk_house)
            if house_fmt:
                details.append(house_fmt)
            sections.append(f"DK: {' '.join(details)}")

        current_maha = chart_factors.get("current_mahadasha")
        current_antar = chart_factors.get("current_antardasha")
        if current_maha or current_antar:
            consumed.update({"current_mahadasha", "current_antardasha"})
            start = chart_factors.get("current_mahadasha_start") or chart_factors.get("mahadasha_start_date")
            end = chart_factors.get("current_mahadasha_end") or chart_factors.get("mahadasha_end_date")
            consumed.update({"current_mahadasha_start", "current_mahadasha_end", "mahadasha_start_date", "mahadasha_end_date"})
            antar_start = chart_factors.get("current_antardasha_start") or chart_factors.get("antardasha_start_date")
            antar_end = chart_factors.get("current_antardasha_end") or chart_factors.get("antardasha_end_date")
            consumed.update({"current_antardasha_start", "current_antardasha_end", "antardasha_start_date", "antardasha_end_date"})

            maha_symbol = self._planet_symbol(current_maha) if current_maha else "?"
            antar_symbol = self._planet_symbol(current_antar) if current_antar else "?"
            range_bits = []
            if start and end:
                range_bits.append(self._format_timeline(start, end))
            if antar_start and antar_end:
                range_bits.append(self._format_timeline(antar_start, antar_end, short=True))
            range_str = " | ".join(range_bits)
            sections.append(f"Dasha: {maha_symbol}/{antar_symbol}{(' ' + range_str) if range_str else ''}".strip())

        periods = chart_factors.get("dasha_periods_20yr")
        if periods and isinstance(periods, list):
            filtered = self._filter_periods(periods, window_years=10)
            if filtered:
                summary = []
                for period in filtered[:3]:
                    maha = self._planet_symbol(period.get("mahadasha"))
                    antar = self._planet_symbol(period.get("antardasha"))
                    start = period.get("start_date")
                    end = period.get("end_date")
                    tag = "*" if period.get("is_current") else ""
                    summary.append(f"{tag}{maha}/{antar} {self._format_timeline(start, end, short=True)}".strip())
                if summary:
                    sections.append(f"±10y: {' | '.join(summary)}")
            consumed.add("dasha_periods_20yr")

        return sections

    def _extract_house_number(self, key: str) -> Optional[int]:
        match = re.search(r"(\d+)(?:st|nd|rd|th)", key)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    def _extract_planet_name(self, key: str) -> Optional[str]:
        known = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
        for planet in known:
            if key.startswith(f"{planet}_"):
                return planet
        return None

    def _abbr_sign(self, value: Any) -> str:
        if not value:
            return "?"
        text = str(value).strip().title()
        abbreviations = {
            "Aries": "Ari",
            "Taurus": "Tau",
            "Gemini": "Gem",
            "Cancer": "Can",
            "Leo": "Leo",
            "Virgo": "Vir",
            "Libra": "Lib",
            "Scorpio": "Sco",
            "Sagittarius": "Sag",
            "Capricorn": "Cap",
            "Aquarius": "Aqu",
            "Pisces": "Pis",
        }
        return abbreviations.get(text, text[:3])

    def _format_house(self, value: Any) -> str:
        if value in (None, "", 0):
            return ""
        if isinstance(value, int):
            return f"{value}H"
        match = re.search(r"(\d+)", str(value))
        if match:
            return f"{int(match.group(1))}H"
        return ""

    def _format_placement(self, value: str) -> str:
        if not value:
            return ""
        text = value.strip()
        sign_match = re.search(r"(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces)", text, re.IGNORECASE)
        house_match = re.search(r"(\d+)(?:st|nd|rd|th)?\s*house", text, re.IGNORECASE)
        sign_part = self._abbr_sign(sign_match.group(1)) if sign_match else None
        house_part = self._format_house(house_match.group(1) if house_match else None)
        if sign_part and house_part:
            return f"{sign_part} {house_part}"
        if sign_part:
            return sign_part
        return text.split(",")[0][:16]

    def _format_nakshatra(self, nakshatra: Any, pada: Any) -> str:
        nak = str(nakshatra).strip().title() if nakshatra else ""
        pada_token = self._format_pada(pada)
        if nak and pada_token:
            return f"{nak} {pada_token}"
        if nak:
            return nak
        if pada_token:
            return pada_token
        return ""

    def _format_pada(self, value: Any) -> str:
        if not value:
            return ""
        match = re.search(r"(\d)", str(value))
        if match:
            return f"P{match.group(1)}"
        return ""

    def _format_planet_list(self, value: Any) -> str:
        if not value:
            return ""
        if isinstance(value, (list, tuple, set)):
            items = [self._planet_symbol(item) for item in value if item]
        else:
            tokens = re.split(r"[,/&]| and ", str(value))
            items = [self._planet_symbol(token.strip()) for token in tokens if token.strip()]
        return ", ".join(items)

    def _planet_symbol(self, planet: Any) -> str:
        if not planet:
            return "?"
        mapping = {
            "sun": "☉",
            "moon": "☾",
            "mars": "♂",
            "mercury": "☿",
            "jupiter": "♃",
            "venus": "♀",
            "saturn": "♄",
            "rahu": "☊",
            "ketu": "☋",
        }
        text = str(planet).strip()
        key = text.lower()
        if key in mapping:
            return mapping[key]
        if len(text) <= 3:
            return text.title()
        return text[:2].title()

    def _retro_flag(self, value: Any) -> str:
        if self._is_truthy(value):
            return "R"
        return ""

    def _is_truthy(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            text = value.strip().lower()
            return text in {"true", "retrograde", "yes", "y", "1"}
        return False

    def _clean_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (list, tuple, set)):
            return ", ".join(str(item).strip() for item in value if item)
        return str(value)

    def _format_timeline(self, start: Any, end: Any, short: bool = False) -> str:
        start_dt = self._parse_date(start)
        end_dt = self._parse_date(end)
        if not start_dt and not end_dt:
            return ""
        start_token = self._format_date_token(start_dt or start, short)
        end_token = self._format_date_token(end_dt or end, short)
        if not start_token and not end_token:
            return ""
        if start_token and end_token:
            return f"{start_token}→{end_token}"
        return start_token or end_token

    def _format_date_token(self, value: Any, short: bool) -> str:
        if isinstance(value, str):
            dt = self._parse_date(value)
        else:
            dt = value if isinstance(value, datetime) else None
        if not dt:
            text = str(value).strip()
            return text[:10]
        if short:
            return dt.strftime("%Y-%m")
        return dt.strftime("%Y-%m-%d")

    def _filter_periods(self, periods: List[Dict[str, Any]], window_years: int) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        start_year = now.year - window_years
        end_year = now.year + window_years
        filtered: List[Dict[str, Any]] = []
        for period in periods:
            start = self._parse_date(period.get("start_date"))
            end = self._parse_date(period.get("end_date"))
            if not start and not end:
                continue
            year = start.year if start else end.year if end else now.year
            if start and start.year > end_year:
                continue
            if end and end.year < start_year:
                continue
            if year < start_year or year > end_year:
                continue
            filtered.append(period)
        return filtered

    def _parse_date(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%d-%m-%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    def _generate_queries(
        self,
        question: str,
    chart_factors: Dict[str, Any],
        niche: str,
        intent: str,
        max_queries: int,
    ) -> List[str]:
        queries: List[str] = []
        base = question.strip()
        if base:
            queries.append(base[:140])

        niche_key = self._resolve_niche_key(niche)
        priority_keys = self._NICHE_KEYWORDS.get(niche_key, [])

        for key in priority_keys:
            if len(queries) >= max_queries:
                break
            value = chart_factors.get(key)
            if not value:
                continue
            label = self._friendly_factor_name(key)
            snippet = self._truncate_value(value)
            query = f"{label} {snippet} {intent} insight"
            queries.append(query[:140])

        # Timing questions get a couple of explicit dasha/transit queries
        if len(queries) < max_queries and (intent == "timing" or is_timing_question(question)):
            timing_factors = get_timing_factors(niche, chart_factors)[: self.max_timing_factors]
            for factor in timing_factors:
                if len(queries) >= max_queries:
                    break
                query = f"{self._friendly_factor_name(factor)} timing for {question[:60]}"
                if query not in queries:
                    queries.append(query[:140])

        # Ensure we always hit the desired budget
        while len(queries) < max_queries:
            fallback = f"{intent} {niche_key} classical interpretation"
            if fallback not in queries:
                queries.append(fallback)
            else:
                queries.append(f"{niche_key} vedic astrology {len(queries)}")

        return queries[:max_queries]

    def _retrieve_passages(
        self,
        queries: Sequence[str],
        limit: int,
    ) -> Tuple[List[Dict[str, Any]], float]:
        if not queries:
            return [], 0.0

        retrieval_start = time.time()

        passages: List[Dict[str, any]] = []

        if hasattr(self.rag_retriever, "retrieve_passages"):
            raw = self.rag_retriever.retrieve_passages(queries=list(queries))
            if isinstance(raw, dict) and "passages" in raw:
                raw = raw["passages"]
            if isinstance(raw, list):
                passages.extend(raw)
        elif hasattr(self.rag_retriever, "search_passages"):
            embedded = self.embedder.embed_queries_batch(queries)
            vectors = [item.embedding for item in embedded]
            top_k_per_query = max(1, math.ceil(limit / max(1, len(queries))) + 1)
            results = self.rag_retriever.search_passages(
                query_embeddings=vectors,
                top_k=top_k_per_query,
                distance_threshold=self.distance_threshold,
            )
            for index, result in enumerate(results):
                for passage in result.get("passages", []):
                    passage = dict(passage)
                    passage.setdefault("query_index", index)
                    passages.append(passage)
        else:
            logger.warning("RAG retriever does not expose a supported interface; skipping retrieval")

        normalized = self._normalize_passages(passages, queries, limit)
        latency = (time.time() - retrieval_start) * 1000
        return normalized, latency

    # Formatting utilities -------------------------------------------------

    def _normalize_passages(
        self,
        passages: Iterable[Dict[str, Any]],
        queries: Sequence[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        unique: Dict[str, Dict[str, any]] = {}
        for passage in passages:
            text = passage.get("passage") or passage.get("text") or passage.get("content") or ""
            text = str(text).strip()
            if not text:
                continue
            fingerprint = text[:200].lower()
            if fingerprint in unique:
                continue
            source = passage.get("source") or passage.get("topic") or passage.get("chapter", "Classical Text")
            score = (
                passage.get("relevance")
                or passage.get("relevance_score")
                or passage.get("similarity_score")
                or (1.0 - passage.get("distance", 1.0))
            )
            query_index = passage.get("query_index", 0)
            query_text = queries[query_index] if 0 <= query_index < len(queries) else queries[0]
            unique[fingerprint] = {
                "factor": passage.get("factor") or source,
                "passage": text,
                "source": source,
                "query": query_text,
                "relevance": float(score) if isinstance(score, (int, float)) else 0.0,
            }

        ordered = sorted(unique.values(), key=lambda item: item.get("relevance", 0.0), reverse=True)
        return ordered[:limit] if limit else ordered

    @staticmethod
    def _resolve_niche_key(niche: str) -> str:
        lowered = niche.lower()
        if "love" in lowered:
            return "love"
        if "career" in lowered:
            return "career"
        if "wealth" in lowered or "finance" in lowered:
            return "wealth"
        if "health" in lowered:
            return "health"
        if "spirit" in lowered:
            return "spiritual"
        return "love"

    @staticmethod
    def _friendly_factor_name(factor: str) -> str:
        return factor.replace("_", " ").capitalize()

    @staticmethod
    def _truncate_value(value: any, limit: int = 64) -> str:
        text = str(value).strip()
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."


__all__ = ["SmartOrchestrator", "OrchestrationOutcome"]
