"""Gemini powered synthesizer for final responses."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types


logger = logging.getLogger(__name__)


class ModernSynthesizer:
    """Creates the final answer using Gemini 2.5 Flash."""

    WORD_TARGETS = {
        "SIMPLE": "300-400 words",
        "MODERATE": "400-500 words",
        "COMPLEX": "600-800 words",
    }

    def __init__(
        self,
        gemini_client: genai.Client,
        model_name: str = "gemini-1.5-flash",
        temperature: float = 0.6,
        max_output_tokens: int = 3000,
        fallback_model: Optional[str] = None,
    ) -> None:
        self.client = gemini_client
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.fallback_model = fallback_model
        self._chart_section_cache: OrderedDict[str, str] = OrderedDict()
        self._chart_section_cache_size = 128
        self._response_cache: OrderedDict[str, str] = OrderedDict()
        self._response_cache_size = 64

    def synthesize_final_response(
        self,
        question: str,
        chart_values: Dict,
        chart_focus: Optional[List[str]] = None,
        classical_knowledge: Optional[List[Dict]] = None,
        niche_instruction: str = "",
        conversation_history: Optional[List[Dict]] = None,
        complexity: str = "SIMPLE",
        validated_knowledge: Optional[Dict] = None,
        mode: str = "draft",  # NEW: "draft" or "expand"
    ) -> str:
        """
        Create the final response tailored to the requested complexity and mode.
        
        NEW: Two-pass generation for speed optimization
        - mode="draft": Fast 300-400 token response (1.5-3s)
        - mode="expand": Full detailed response (14-17s)
        """

        complexity = complexity.upper()
        word_target = self.WORD_TARGETS.get(complexity, self.WORD_TARGETS["MODERATE"])
        
        # OPTIMIZATION: Override word target and tokens for draft mode
        if mode == "draft":
            word_target = "150-250 words (4-6 concise bullets)"
            draft_max_tokens = 4000  # CRITICAL: Gemini 2.5 Flash uses thoughts (1500 tokens) + response (400-800 tokens)
            draft_temperature = 0.3  # Slightly higher for natural flow
            logger.info("🚀 DRAFT MODE: max_tokens=4000 (includes thinking), temp=0.3")
        else:
            word_target = self.WORD_TARGETS.get(complexity, self.WORD_TARGETS["MODERATE"])
            draft_max_tokens = 6000  # CRITICAL: Same as draft - needs room for thinking (2400) + detailed response (1500-2000)
            draft_temperature = self.temperature
            logger.info(f"📚 EXPAND MODE: max_tokens=6000 (includes thinking), temp={self.temperature}")

        history_text = self._format_history(conversation_history)
        chart_section = self._format_chart_section(chart_values, chart_focus, complexity)
        selected_references = self._select_classical_passages(question, classical_knowledge, complexity)
        references_section = self._format_classical(selected_references, complexity)

        timing_instruction = ""
        if self._is_timing_question(question):
            timing_instruction = (
                "- Prioritize Vimshottari Dasha timelines, cite specific start/end dates.\n"
                "- Reference Jupiter/Saturn transits that activate the houses involved.\n"
            )

        model_alias = self._model_alias(self.model_name)
        prompt = self._build_prompt(
            question=question,
            niche_instruction=niche_instruction,
            chart_section=chart_section,
            references_section=references_section,
            history_text=history_text,
            timing_instruction=timing_instruction,
            word_target=word_target,
            model_alias=model_alias,
            mode=mode,  # Pass mode to prompt builder
        )
        
        # DIAGNOSTIC: Log prompt length to identify if it's consuming all tokens
        prompt_length = len(prompt)
        estimated_tokens = prompt_length // 4  # Rough estimate: 4 chars per token
        logger.info(f"Prompt length: {prompt_length} chars (~{estimated_tokens} tokens), max_tokens: {draft_max_tokens}")
        if estimated_tokens > draft_max_tokens * 0.8:
            logger.warning(f"⚠️ Prompt consuming {estimated_tokens}/{draft_max_tokens} tokens! Only {draft_max_tokens - estimated_tokens} tokens left for response!")

        cached_response = self._response_cache_get(prompt)
        if cached_response is not None:
            return cached_response

        try:
            generated = self._generate(
                prompt, 
                self.model_name,
                max_tokens=draft_max_tokens,
                temperature=draft_temperature
            )
            if generated:
                self._response_cache_set(prompt, generated)
                return generated
        except Exception as exc:  # pragma: no cover - defensive fallback
            if self._should_retry_with_fallback(exc):
                fallback_model = self.fallback_model
                fallback_alias = self._model_alias(fallback_model)
                logger.warning(
                    "Primary model %s unavailable (%s). Retrying with fallback model %s.",
                    self.model_name,
                    exc,
                    fallback_model,
                )
                fallback_prompt = self._build_prompt(
                    question=question,
                    niche_instruction=niche_instruction,
                    chart_section=chart_section,
                    references_section=references_section,
                    history_text=history_text,
                    timing_instruction=timing_instruction,
                    word_target=word_target,
                    model_alias=fallback_alias,
                )
                try:
                    generated = self._generate(fallback_prompt, fallback_model)
                    if generated:
                        self._response_cache_set(prompt, generated)
                        return generated
                except Exception as fallback_exc:  # pragma: no cover - defensive fallback
                    logger.error("Fallback model %s also failed: %s", fallback_model, fallback_exc)
            else:
                logger.error("ModernSynthesizer error: %s", exc)

        fallback = self._get_fallback_response(question, chart_values)
        self._response_cache_set(prompt, fallback)
        return fallback

    def _generate(
        self, 
        prompt: str, 
        model_name: Optional[str],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Optional[str]:
        if not model_name:
            return None

        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature if temperature is not None else self.temperature,
                    max_output_tokens=max_tokens if max_tokens is not None else self.max_output_tokens,
                ),
            )

            response_text = self._extract_text(response)
            if not response_text:
                logger.warning("Empty response text from model %s", model_name)
                return None

            final_text = self._post_process(response_text)
            return final_text
        except Exception as e:
            logger.error("Error in _generate with model %s: %s", model_name, e, exc_info=True)
            raise  # Re-raise to trigger fallback logic

    def _build_prompt(
        self,
        *,
        question: str,
        niche_instruction: str,
        chart_section: str,
        references_section: str,
        history_text: str,
        timing_instruction: str,
        word_target: str,
        model_alias: str,
        mode: str = "draft",
    ) -> str:
        references_text = references_section if references_section else "None provided for this question."
        history_block = history_text if history_text else "None"
        
        # OPTIMIZATION: Aggressively truncate for draft mode to reduce prompt tokens
        if mode == "draft":
            # Truncate classical references to 400 chars (save ~150 tokens)
            if len(references_text) > 400:
                references_text = references_text[:400] + "\n...(truncated for speed)"
            # Truncate chart section to 800 chars (save ~200 tokens)
            if len(chart_section) > 800:
                chart_section = chart_section[:800] + "\n...(truncated for speed)"
            # Truncate niche instruction to 300 chars
            if len(niche_instruction) > 300:
                niche_instruction = niche_instruction[:300] + "..."
            logger.debug("Draft mode: Truncated prompt sections to save tokens")
        
        # Detect question type for tailored instructions
        question_lower = question.lower()
        is_appearance = any(word in question_lower for word in ["look", "appearance", "beautiful", "handsome", "attractive"])
        is_personality = any(word in question_lower for word in ["personality", "nature", "character", "behavior", "like"])
        is_timing = self._is_timing_question(question)
        is_compatibility = any(word in question_lower for word in ["compatible", "match", "relationship", "get along"])

        # Base instructions (adapt based on mode)
        if mode == "draft":
            # DRAFT MODE: Concise, structured, fast
            instructions = [
                f"- Produce {word_target}. Use 4-6 BULLET POINTS with clear insights.",
                "- Structure: 🔮 Quick Answer (2-3 sentences) + 4-6 key bullets + 📝 Summary (1-2 sentences).",
                "- CRITICAL: Base your analysis ONLY on the specific chart factors provided below.",
                "- Be CONCISE but SPECIFIC. Provide actionable insights, not generic statements.",
                "- Each bullet should give one concrete detail with astrological reasoning.",
                "- Target: 300-400 words total for completeness.",
            ]
        else:
            # EXPAND MODE: Detailed, comprehensive
            instructions = [
                f"- Produce {word_target}. Structure: 🔮 Quick Answer (2-3 sentences), detailed analysis, 📝 Summary, 💡 Follow-ups.",
                "- CRITICAL: Base your analysis ONLY on the specific chart factors provided below. Do NOT make up placements.",
                "- Pull explicit placements from the chart data (e.g., '7th lord Jupiter in Aquarius').",
                "- When classical references are provided, cite them inline (e.g., 'BPHS states...').",
                "- Use a warm, conversational tone while maintaining expertise.",
            ]

        # Add question-specific instructions
        if is_appearance:
            instructions.extend([
                "- For appearance analysis: Focus on 7th house, 7th lord, Venus/Jupiter, Darakaraka, relevant Nakshatras.",
                "- Describe: build/height, facial features, complexion, style based on signs, planets, and aspects.",
                "- Cross-verify with D9 (Navamsa) chart factors if provided.",
            ])
        
        if is_personality:
            instructions.extend([
                "- For personality analysis: Synthesize Moon sign, Ascendant, 7th lord, Venus, and planetary aspects.",
                "- Describe behavioral traits, emotional nature, intellectual qualities, and social style.",
                "- Include both strengths and areas for growth.",
            ])
        
        if is_timing:
            instructions.extend([
                "- For timing predictions: Prioritize Vimshottari Dasha periods (Maha/Antar/Pratyantar).",
                "- Reference current running Dasha and upcoming favorable periods.",
                "- Cite specific months/years when transits (Jupiter/Saturn) activate relevant houses.",
                "- If exact dates unavailable, give realistic ranges (e.g., 'Q2 2025' or '2025-2026').",
            ])
        
        if is_compatibility:
            instructions.extend([
                "- For compatibility: Compare Moon signs, Ascendants, Venus-Mars placements, 7th house factors.",
                "- Discuss emotional, intellectual, and physical compatibility separately.",
                "- Mention challenges and how to navigate them.",
            ])

        # Add general reminders
        instructions.extend([
            "- If chart data is insufficient for a specific point, provide the best possible answer based on available information, then acknowledge what additional data would help.",
            "- Avoid generic statements; be specific to THIS chart.",
            "- Use emojis sparingly (only for section headers).",
        ])

        if timing_instruction:
            instructions.extend(line.strip() for line in timing_instruction.strip().splitlines() if line.strip())

        instructions_text = "\n".join(instructions)

        return f"""You are a master Vedic astrologer using {model_alias}. Answer this question with precision and depth.

**User's Question:**
{question}

**Niche Context:**
{niche_instruction}

**Chart Data:**
{chart_section}

**Classical References:**
{references_text}

**Conversation History:**
{history_block}

**Your Task:**
{instructions_text}

**Response:**
"""

    def _should_retry_with_fallback(self, exc: Exception) -> bool:
        if not self.fallback_model or self.fallback_model == self.model_name:
            return False

        message = getattr(exc, "message", None) or str(exc)
        message_upper = message.upper()
        return "NOT_FOUND" in message_upper or "404" in message_upper

    @staticmethod
    def _model_alias(model_name: Optional[str]) -> str:
        if not model_name:
            return "Gemini"

        aliases = {
            "gemini-1.5-flash": "Gemini 2.5 Flash",
            "gemini-2.5-pro": "Gemini 2.5 Pro",
            "gemini-1.5-pro": "Gemini 1.5 Pro",
            "gemini-1.5-pro-001": "Gemini 1.5 Pro",
            "gemini-1.5-flash": "Gemini 1.5 Flash",
            "gemini-2.0-flash": "Gemini 2.0 Flash",
        }

        return aliases.get(model_name, model_name)
    
    def _post_process(self, text: str) -> str:
        """Clean up response formatting"""
        if text is None:
            return ""
        
        # Remove excessive asterisks
        text = text.replace("***", "")
        while "****" in text:
            text = text.replace("****", "**")
        
        # Remove symbol walls
        text = text.replace("=" * 20, "")
        text = text.replace("-" * 20, "")
        
        # Remove excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _format_chart_section(self, values: Dict, chart_focus: Optional[List[str]], complexity: str) -> str:
        """
        Format chart factors with intelligent grouping by chart type (D1, D9, D10, Dashas, etc.)
        """
        cache_key = self._chart_section_cache_key(chart_focus, values, complexity)
        cached = self._chart_section_cache_get(cache_key)
        if cached is not None:
            return cached

        if chart_focus:
            # Organize chart_focus into logical sections
            sections = {
                "D1 (Rasi) Chart": [],
                "D9 (Navamsa) Chart": [],
                "D10 (Dasamsa) Chart": [],
                "Other Divisional Charts": [],
                "Vimshottari Dasha": [],
                "Yogas & Special Combinations": [],
                "Planetary Details": [],
            }
            
            for entry in chart_focus:
                entry_lower = entry.lower()
                if "d9" in entry_lower or "navamsa" in entry_lower:
                    sections["D9 (Navamsa) Chart"].append(entry)
                elif "d10" in entry_lower or "dasamsa" in entry_lower:
                    sections["D10 (Dasamsa) Chart"].append(entry)
                elif any(f"d{i}" in entry_lower for i in [2, 3, 4, 7, 12, 16, 20, 24, 27, 30, 40, 45, 60]):
                    sections["Other Divisional Charts"].append(entry)
                elif any(word in entry_lower for word in ["dasha", "mahadasha", "antardasha", "pratyantara"]):
                    sections["Vimshottari Dasha"].append(entry)
                elif "yoga" in entry_lower or "combination" in entry_lower:
                    sections["Yogas & Special Combinations"].append(entry)
                elif any(word in entry_lower for word in ["nakshatra", "pada", "retrograde", "karaka"]):
                    sections["Planetary Details"].append(entry)
                else:
                    sections["D1 (Rasi) Chart"].append(entry)
            
            # Build formatted output
            formatted_lines = []
            for section_name, entries in sections.items():
                if entries:
                    formatted_lines.append(f"\n**{section_name}:**")
                    for entry in entries:
                        formatted_lines.append(f"  - {entry}")
            
            result = "\n".join(formatted_lines) if formatted_lines else "\n".join(f"- {e}" for e in chart_focus)
            self._chart_section_cache_set(cache_key, result)
            return result

        # Fallback to legacy formatting if highlights missing
        if not values:
            result = "No chart values"
            self._chart_section_cache_set(cache_key, result)
            return result
        
        max_items = {"SIMPLE": 50, "MODERATE": 80, "COMPLEX": 150}.get(complexity.upper(), 50)
        lines = []
        for index, (key, value) in enumerate(values.items()):
            if index >= max_items:
                break
            if not value:
                continue
            lines.append(f"- {key}: {value}")
        result = "\n".join(lines)
        self._chart_section_cache_set(cache_key, result)
        return result

    def _chart_section_cache_key(
        self,
        chart_focus: Optional[List[str]],
        values: Optional[Dict],
        complexity: str,
    ) -> str:
        payload = {"complexity": complexity}
        if chart_focus:
            payload["focus"] = chart_focus
        elif values:
            payload["values"] = self._normalize_for_cache(values)
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha1(blob.encode("utf-8")).hexdigest()

    def _chart_section_cache_get(self, key: str) -> Optional[str]:
        cached = self._chart_section_cache.get(key)
        if cached is None:
            return None
        self._chart_section_cache.move_to_end(key)
        return cached

    def _chart_section_cache_set(self, key: str, value: str) -> None:
        self._chart_section_cache[key] = value
        self._chart_section_cache.move_to_end(key)
        while len(self._chart_section_cache) > self._chart_section_cache_size:
            self._chart_section_cache.popitem(last=False)

    def _response_cache_get(self, prompt: str) -> Optional[str]:
        key = self._hash_text(prompt)
        cached = self._response_cache.get(key)
        if cached is None:
            return None
        self._response_cache.move_to_end(key)
        return cached

    def _response_cache_set(self, prompt: str, value: str) -> None:
        key = self._hash_text(prompt)
        self._response_cache[key] = value
        self._response_cache.move_to_end(key)
        while len(self._response_cache) > self._response_cache_size:
            self._response_cache.popitem(last=False)

    def _hash_text(self, text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def _normalize_for_cache(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self._normalize_for_cache(v) for k, v in sorted(value.items())}
        if isinstance(value, (list, tuple, set)):
            return [self._normalize_for_cache(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def _select_classical_passages(
        self,
        question: str,
        knowledge: Optional[List[Dict]],
        complexity: str,
    ) -> List[Dict]:
        if not knowledge:
            return []

        top_k = {"SIMPLE": 3, "MODERATE": 5, "COMPLEX": 8}.get(complexity.upper(), 5)
        question_tokens = self._token_set(question)
        ranked: List[Tuple[float, int, Dict]] = []
        fingerprints: set[str] = set()

        for index, item in enumerate(knowledge):
            if not isinstance(item, dict):
                continue
            passage = str(item.get("passage", "")).strip()
            if not passage:
                continue

            fingerprint = passage[:180].lower()
            if fingerprint in fingerprints:
                continue

            base_score = item.get("relevance") or item.get("relevance_score")
            try:
                score = float(base_score)
            except (TypeError, ValueError):
                score = 0.0

            query_text = str(item.get("query", ""))
            passage_tokens = self._token_set(passage)
            query_tokens = self._token_set(query_text)
            overlap_tokens = question_tokens & (passage_tokens | query_tokens)
            score += 0.35 * len(overlap_tokens)

            distance = item.get("distance")
            if isinstance(distance, (int, float)) and distance > 0:
                score += max(0.0, 1.0 - float(distance))

            length_penalty = min(len(passage), 900) / 900.0
            score += 0.15 * (1.0 - length_penalty)

            ranked.append((score, index, item))
            fingerprints.add(fingerprint)

        ranked.sort(key=lambda entry: (-entry[0], entry[1]))
        return [entry[2] for entry in ranked[:top_k]]

    def _format_classical(self, knowledge: Optional[List[Dict]], complexity: str) -> str:
        if not knowledge:
            return ""

        # For SIMPLE love/timing questions, include at least 3 passages
        limit = {"SIMPLE": 3, "MODERATE": 6, "COMPLEX": 8}.get(complexity.upper(), 6)
        truncated = knowledge[:limit]

        formatted: List[str] = []
        for item in truncated:
            passage = str(item.get("passage", "")).strip()
            if not passage:
                continue
            source = item.get("source") or item.get("factor", "Classical Reference")
            query = item.get("query", "")
            formatted.append(
                f"- Source: {source}\n  Insight: {passage[:220]}{'...' if len(passage) > 220 else ''}\n  Query: {query[:120]}"
            )

        return "\n".join(formatted)

    def _token_set(self, text: str) -> set[str]:
        if not text:
            return set()
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return {token for token in tokens if len(token) > 2}
    
    def _get_fallback_response(self, question: str, chart_values: dict) -> str:
        """Generate fallback response if synthesis fails"""
        
        return f"""🔮 Quick Answer

Based on your chart, I can provide insights about: "{question}"

**Chart Values:**
{chr(10).join(f"• {k}: {v}" for k, v in list(chart_values.items())[:5])}

**Analysis:**

I've analyzed the key astrological factors in your chart. While technical limitations prevented full retrieval of classical references, the fundamental indicators show specific patterns relevant to your question.

📝 Summary

The synthesis process encountered issues, but core astrological factors have been identified.

💡 Follow-up

Would you like me to focus on a specific aspect? Please ask a more targeted question for detailed insights.

⚠️ **Note:** This is a fallback response. For best results, ensure chart data is complete.
"""

    @staticmethod
    def _format_history(history: Optional[List[Dict]]) -> str:
        if not history:
            return ""
        snippets = []
        for exchange in history[-2:]:
            message = exchange.get("user_message") or ""
            reply = exchange.get("assistant_response") or ""
            snippets.append(f"- Q: {message[:80]}\n  A: {reply[:80]}")
        return "\n".join(snippets)

    @staticmethod
    def _is_timing_question(question: str) -> bool:
        lowered = question.lower()
        keywords = ["when", "timing", "period", "date", "month", "year", "timeline", "dasha"]
        return any(keyword in lowered for keyword in keywords)

    @staticmethod
    def _extract_text(response) -> str:
        """Extract text from Gemini response with comprehensive fallback handling."""
        try:
            # FIRST: Try the most direct method - response.text
            # This works for complete responses and some MAX_TOKENS cases
            if hasattr(response, "text"):
                try:
                    text = response.text
                    if text:
                        return text
                except (ValueError, AttributeError) as e:
                    # response.text may throw ValueError if candidates have no text
                    logger.debug("response.text failed: %s", e)
            
            # SECOND: Manually extract from candidates structure
            collected: List[str] = []
            
            # Check if response was truncated at MAX_TOKENS
            max_tokens_hit = False
            if hasattr(response, "candidates") and response.candidates:
                first_candidate = response.candidates[0]
                if hasattr(first_candidate, "finish_reason"):
                    finish_reason = str(first_candidate.finish_reason)
                    if "MAX_TOKENS" in finish_reason:
                        max_tokens_hit = True
                        logger.warning("Response truncated at MAX_TOKENS. Collecting partial response...")

            # Iterate through candidates and collect any text chunks
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    # Try candidate.text first (most direct)
                    try:
                        candidate_text = candidate.text
                        if candidate_text:
                            collected.append(candidate_text)
                            continue
                    except (ValueError, AttributeError) as e:
                        logger.debug("candidate.text failed: %s", e)
                    
                    # Try accessing content.parts
                    content = getattr(candidate, "content", None)
                    if content:
                        # DEBUG: Log parts info
                        parts_attr = getattr(content, "parts", None)
                        if parts_attr is not None:
                            logger.debug("Parts found: type=%s, len=%d", type(parts_attr), len(parts_attr) if hasattr(parts_attr, '__len__') else -1)
                            # Try to iterate even if length is 0 (might be lazy-loaded)
                            part_count = 0
                            for part in parts_attr:
                                part_count += 1
                                part_text = getattr(part, "text", None)
                                if part_text:
                                    logger.debug("Found text in part %d: %d chars", part_count, len(part_text))
                                    collected.append(part_text)
                                elif hasattr(part, "model_dump"):
                                    try:
                                        dump = part.model_dump()
                                        maybe_text = dump.get("text")
                                        if maybe_text:
                                            logger.debug("Found text in part.model_dump %d: %d chars", part_count, len(maybe_text))
                                            collected.append(maybe_text)
                                    except Exception as e:
                                        logger.debug("part.model_dump failed: %s", e)
                            if part_count == 0:
                                logger.warning("parts attribute exists but iteration yielded 0 parts")
                        else:
                            logger.debug("content.parts is None")
                    
                    # If we got text, move to next candidate
                    if collected:
                        continue

                    # Fallback to model_dump if direct attributes were empty
                    try:
                        candidate_dump = candidate.model_dump()
                        if candidate_dump:
                            content_dump = candidate_dump.get("content") or {}
                            parts = content_dump.get("parts") or []
                            for part in parts:
                                if not isinstance(part, dict):
                                    continue
                                part_text = part.get("text")
                                if part_text:
                                    collected.append(part_text)
                    except (AttributeError, Exception) as e:
                        logger.debug("candidate.model_dump failed: %s", e)

            # If we collected text (even partial), use it
            if collected:
                merged = "\n\n".join(chunk.strip() for chunk in collected if chunk and chunk.strip())
                if merged.strip():
                    logger.info("Successfully extracted %d characters from response", len(merged))
                    return merged.strip()
            
            # THIRD: Try response.model_dump() as last resort
            try:
                response_dump = response.model_dump()
                logger.error("Full response.model_dump(): %s", json.dumps(response_dump, indent=2, default=str)[:2000])
                candidates = response_dump.get("candidates", [])
                for candidate in candidates:
                    content = candidate.get("content", {})
                    parts = content.get("parts", [])
                    logger.error("Candidate parts from dump: %s", parts)
                    for part in parts:
                        if isinstance(part, dict):
                            text = part.get("text")
                            if text:
                                logger.info("Extracted text from response.model_dump()")
                                return text
            except Exception as e:
                logger.debug("response.model_dump() extraction failed: %s", e)
            
            # Only log error if truly no text found
            logger.error("CRITICAL: Could not extract ANY text from response!")
            logger.error("Response type: %s", type(response))
            if hasattr(response, "candidates"):
                logger.error("Candidates count: %d", len(response.candidates) if response.candidates else 0)
                if response.candidates:
                    cand = response.candidates[0]
                    logger.error("First candidate finish_reason: %s", getattr(cand, "finish_reason", "N/A"))
                    logger.error("First candidate has content: %s", hasattr(cand, "content"))
                    if hasattr(cand, "content"):
                        content = cand.content
                        logger.error("Content has parts: %s", hasattr(content, "parts"))
                        if hasattr(content, "parts"):
                            logger.error("Parts count: %d", len(content.parts) if content.parts else 0)
            
            # Try one more time with str() conversion
            try:
                response_str = str(response)
                if "text:" in response_str or "text=" in response_str:
                    logger.error("Response string contains 'text' field but extraction failed!")
                    logger.error("Response string preview: %s", response_str[:500])
            except Exception:
                pass
                
            return ""
        except Exception as e:
            logger.error("Error extracting text from response: %s", e, exc_info=True)
            return ""
