"""OpenRouter GPT-4.1 Mini synthesizer for final responses."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

import requests


logger = logging.getLogger(__name__)


class OpenRouterSynthesizer:
    """Creates final answers using OpenAI GPT-4.1 Mini via OpenRouter."""

    WORD_TARGETS = {
        "SIMPLE": "300-400 words",
        "MODERATE": "400-500 words",
        "COMPLEX": "600-800 words",
    }

    def __init__(
        self,
        api_key: str = "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",
        model_name: str = "openai/gpt-4.1-mini",
        temperature: float = 0.6,
        max_output_tokens: int = 2000,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
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
        mode: str = "draft",
    ) -> str:
        """
        Create final response using GPT-4.1 Mini via OpenRouter.
        
        - mode="draft": Fast 300-400 token response (1-2s)
        - mode="expand": Full detailed response (3-5s)
        """

        complexity = complexity.upper()
        word_target = self.WORD_TARGETS.get(complexity, self.WORD_TARGETS["MODERATE"])
        
        # OPTIMIZATION: Token budgets for GPT-4.1 Mini
        if mode == "draft":
            word_target = "150-250 words (4-6 concise bullets)"
            max_tokens = 500  # GPT-4.1 Mini is very efficient, no thinking overhead!
            temperature = 0.2
            logger.info("🚀 DRAFT MODE: max_tokens=500 (GPT-4.1 Mini), temp=0.2")
        else:
            word_target = self.WORD_TARGETS.get(complexity, self.WORD_TARGETS["MODERATE"])
            max_tokens = 1500  # Detailed response
            temperature = self.temperature
            logger.info(f"📚 EXPAND MODE: max_tokens=1500 (GPT-4.1 Mini), temp={self.temperature}")

        history_text = self._format_history(conversation_history)
        chart_section = self._format_chart_section(chart_values, chart_focus, complexity)
        selected_references = self._select_classical_passages(question, classical_knowledge, complexity)
        references_section = self._format_classical(selected_references, complexity)
        syn_section = self._format_syn_procedures(validated_knowledge)

        timing_instruction = ""
        if self._is_timing_question(question):
            timing_instruction = (
                "- Prioritize Vimshottari Dasha timelines, cite specific start/end dates.\n"
                "- Reference Jupiter/Saturn transits that activate the houses involved.\n"
            )

        prompt = self._build_prompt(
            question=question,
            niche_instruction=niche_instruction,
            chart_section=chart_section,
            references_section=references_section,
            syn_section=syn_section,
            history_text=history_text,
            timing_instruction=timing_instruction,
            word_target=word_target,
            mode=mode,
        )
        
        # Diagnostic logging
        prompt_length = len(prompt)
        estimated_tokens = prompt_length // 4
        logger.info(f"Prompt length: {prompt_length} chars (~{estimated_tokens} tokens), max_tokens: {max_tokens}")

        cached_response = self._response_cache_get(prompt)
        if cached_response is not None:
            logger.info("Cache hit! Returning cached response")
            return cached_response

        try:
            generated = self._generate(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            if generated:
                self._response_cache_set(prompt, generated)
                return generated
        except Exception as exc:
            logger.error("OpenRouter synthesis error: %s", exc, exc_info=True)

        fallback = self._get_fallback_response(question, chart_values)
        self._response_cache_set(prompt, fallback)
        return fallback

    def _generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Generate response using OpenRouter GPT-4.1 Mini."""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://astroairk.com",
                "X-Title": "AstroAirk",
            }

            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.95,
            }

            logger.info(f"Calling OpenRouter API with model={self.model_name}, max_tokens={max_tokens}")
            
            response = requests.post(
                url=self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            if "error" in result:
                logger.error("OpenRouter API error: %s", result["error"])
                return None

            if "choices" not in result or not result["choices"]:
                logger.error("No choices in OpenRouter response")
                return None

            message_content = result["choices"][0].get("message", {}).get("content", "")
            
            if not message_content:
                logger.warning("Empty response from OpenRouter")
                return None

            # Log token usage
            usage = result.get("usage", {})
            logger.info(
                f"Tokens used: input={usage.get('prompt_tokens', 0)}, "
                f"output={usage.get('completion_tokens', 0)}, "
                f"total={usage.get('total_tokens', 0)}"
            )

            final_text = self._post_process(message_content)
            return final_text

        except requests.exceptions.RequestException as e:
            logger.error("OpenRouter request failed: %s", e)
            return None
        except Exception as e:
            logger.error("Error in _generate: %s", e, exc_info=True)
            return None

    def _build_prompt(
        self,
        *,
        question: str,
        niche_instruction: str,
        chart_section: str,
        references_section: str,
        syn_section: str = "",
        history_text: str,
        timing_instruction: str,
        word_target: str,
        mode: str = "draft",
    ) -> str:
        """Build prompt for GPT-4.1 Mini."""
        
        references_text = references_section if references_section else "None provided for this question."
        history_block = history_text if history_text else "None"
        
        # Aggressive truncation for draft mode
        if mode == "draft":
            if len(references_text) > 400:
                references_text = references_text[:400] + "\n...(truncated for speed)"
            if len(chart_section) > 800:
                chart_section = chart_section[:800] + "\n...(truncated for speed)"
            if len(niche_instruction) > 300:
                niche_instruction = niche_instruction[:300] + "..."
            logger.debug("Draft mode: Truncated prompt sections")
        
        # Detect question type
        question_lower = question.lower()
        is_appearance = any(word in question_lower for word in ["look", "appearance", "beautiful", "handsome", "attractive"])
        is_personality = any(word in question_lower for word in ["personality", "nature", "character", "behavior", "like"])
        is_timing = self._is_timing_question(question)
        is_compatibility = any(word in question_lower for word in ["compatible", "match", "relationship", "get along"])

        # Base instructions
        if mode == "draft":
            instructions = [
                f"- Produce {word_target}. Use 4-6 BULLET POINTS with clear insights.",
                "- Structure: 🔮 Quick Answer (2-3 sentences) + 4-6 key bullets + 📝 Summary (1-2 sentences).",
                "- CRITICAL: Base your analysis ONLY on the specific chart factors provided below.",
                "- Be CONCISE but SPECIFIC. Provide actionable insights, not generic statements.",
                "- Each bullet should give one concrete detail with astrological reasoning.",
                "- Target: 300-400 words total for completeness.",
            ]
        else:
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

        # Add SYN-specific instructions if procedures are provided
        if syn_section:
            instructions.extend([
                "",
                "**CRITICAL - SYN Evaluation Procedure:**",
                "- SYN procedures below are deterministic evaluation rules from expert practitioners.",
                "- Apply each SYN rule systematically to the specific chart factors above.",
                "- Format: 'Per SYN rule [brief description], your chart shows [specific placements], therefore [insight]'",
                "- Example: 'Per SYN rule \"Venus in airy sign → modern partner\", your Venus is in Aquarius (D1) & Pisces (D9), therefore your spouse is unconventional and humanitarian.'",
                "- Follow SYN guidance as structured methodology, but allow reasonable flexibility based on chart context.",
                "- If multiple SYN rules apply, synthesize them into coherent narrative.",
            ])

        instructions.extend([
            "- If chart data is insufficient for a specific point, provide the best possible answer based on available information, then acknowledge what additional data would help.",
            "- Avoid generic statements; be specific to THIS chart.",
            "- Use emojis sparingly (only for section headers).",
        ])

        if timing_instruction:
            instructions.extend(line.strip() for line in timing_instruction.strip().splitlines() if line.strip())

        instructions_text = "\n".join(instructions)

        # Build prompt sections
        prompt_sections = [
            "You are a master Vedic astrologer. Answer this question with precision and depth.",
            "",
            "**User's Question:**",
            question,
            "",
            "**Niche Context:**",
            niche_instruction,
            "",
            "**Chart Data:**",
            chart_section,
        ]

        # Add SYN section if available
        if syn_section:
            prompt_sections.extend([
                "",
                syn_section,
            ])

        # Add classical references
        prompt_sections.extend([
            "",
            "**Classical References:**",
            references_text,
            "",
            "**Conversation History:**",
            history_block,
            "",
            "**Your Task:**",
            instructions_text,
            "",
            "**Response:**",
        ])

        return "\n".join(prompt_sections)

    def _post_process(self, text: str) -> str:
        """Clean up response formatting."""
        if text is None:
            return ""
        
        text = text.replace("***", "")
        while "****" in text:
            text = text.replace("****", "**")
        
        text = text.replace("=" * 20, "")
        text = text.replace("-" * 20, "")
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    def _format_chart_section(self, values: Dict, chart_focus: Optional[List[str]], complexity: str) -> str:
        """Format chart factors intelligently."""
        cache_key = self._chart_section_cache_key(chart_focus, values, complexity)
        cached = self._chart_section_cache_get(cache_key)
        if cached is not None:
            return cached

        if chart_focus:
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
            
            formatted_lines = []
            for section_name, entries in sections.items():
                if entries:
                    formatted_lines.append(f"\n**{section_name}:**")
                    for entry in entries:
                        formatted_lines.append(f"  - {entry}")
            
            result = "\n".join(formatted_lines) if formatted_lines else "\n".join(f"- {e}" for e in chart_focus)
            self._chart_section_cache_set(cache_key, result)
            return result

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

    def _chart_section_cache_key(self, chart_focus: Optional[List[str]], values: Optional[Dict], complexity: str) -> str:
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
        """Select top classical passages for this question."""
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
        """Format classical references."""
        if not knowledge:
            return ""

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

    def _format_syn_procedures(self, validated_knowledge: Optional[Dict]) -> str:
        """Format SYN evaluation procedures with clear instructions for rule-following."""
        if not validated_knowledge or "syn_procedures" not in validated_knowledge:
            return ""

        syn_procedures = validated_knowledge["syn_procedures"]
        if not syn_procedures:
            return ""

        formatted: List[str] = []
        formatted.append("## SYN Evaluation Procedures (Apply Systematically)\n")
        formatted.append("These are deterministic evaluation rules. Apply each rule to the specific chart factors provided above.\n")
        formatted.append("Format your analysis as: 'Per SYN rule [brief rule], your chart shows [specific factor], therefore [insight]'\n")
        
        for idx, proc in enumerate(syn_procedures, 1):
            content = proc.get("content", "").strip()
            section = proc.get("section", "Unknown")
            score = proc.get("score", 0.0)
            
            # Truncate long procedures
            if len(content) > 300:
                content = content[:300] + "..."
            
            formatted.append(f"\n**Rule {idx}** (from {section}, relevance: {score:.2f}):")
            formatted.append(f"{content}")
        
        return "\n".join(formatted)

    def _token_set(self, text: str) -> set[str]:
        """Extract token set from text."""
        if not text:
            return set()
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return {token for token in tokens if len(token) > 2}
    
    def _get_fallback_response(self, question: str, chart_values: dict) -> str:
        """Generate fallback response if synthesis fails."""
        
        return f"""🔮 Quick Answer

Based on your chart, I can provide insights about: "{question}"

**Chart Values:**
{chr(10).join(f"• {k}: {v}" for k, v in list(chart_values.items())[:5])}

**Analysis:**

I've analyzed the key astrological factors in your chart. The fundamental indicators show specific patterns relevant to your question.

📝 Summary

Core astrological factors have been identified based on your chart.

💡 Follow-up

Would you like me to focus on a specific aspect? Please ask a more targeted question for detailed insights.

⚠️ **Note:** This is a fallback response. For best results, ensure chart data is complete.
"""

    @staticmethod
    def _format_history(history: Optional[List[Dict]]) -> str:
        """Format conversation history."""
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
        """Check if question is about timing."""
        lowered = question.lower()
        keywords = ["when", "timing", "period", "date", "month", "year", "timeline", "dasha"]
        return any(keyword in lowered for keyword in keywords)
