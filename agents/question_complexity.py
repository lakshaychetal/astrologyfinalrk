"""Utility module for classifying astrology questions by complexity.

The Smart orchestrator funnels questions into SIMPLE, MODERATE or COMPLEX
tracks. 90% of questions should flow through the SIMPLE path (no RAG), 8%
through MODERATE (light RAG) and 2% through COMPLEX (full RAG).  The
classifier relies on fast regex heuristics so we avoid unnecessary model
calls in the hot path.  A secondary LLM-based classifier can be plugged in
later if accuracy needs improve.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Optional


@dataclass
class ClassificationResult:
    """Structured result returned by :class:`QuestionComplexityClassifier`."""

    complexity: str
    intent: str
    confidence: float
    reasoning: str


class QuestionComplexityClassifier:
    """Fast heuristic classifier for routing questions to the right path."""

    _SIMPLE_PATTERNS: Dict[str, Iterable[str]] = {
        "appearance": [
            r"\b(look|looks|appearance|face|physical|physique|build|height|complexion)\b",
            r"\b(spouse|partner|wife|husband)\b.*\b(look|appearance)\b",
        ],
        "personality": [
            r"\b(personality|nature|character|behavio[u]?r|temperament|traits)\b",
            r"\bwhat\b.*\bkind of\b.*\b(spouse|partner|person)\b",
        ],
        "basic_timing": [
            r"\bwhen\b.*\b(marry|marriage|meet|union|wedding)\b",
            r"\b(soon|timing|timeframe|time frame|period)\b.*\b(marriage|meet)\b",
        ],
        "career": [
            r"\b(career|job|profession|work|business)\b",
            r"\bwhat\b.*\b(job|career|profession|work)\b",
        ],
        "general": [
            r"\b(strength|weakness|quality|trait|indicator)\b",
            r"\b(good|bad|favourable|favorable|unfavourable|unfavorable)\b.*\b(time|period|phase|dasha)\b",
        ],
    }

    _COMPLEX_PATTERNS: Dict[str, Iterable[str]] = {
        "multi_chart": [
            r"\b(d1|d9|d10|d7|divisional|navamsa|dasamsa|saptamsa)\b.*\b(and|with|together|combine|compare|vs)\b",
            r"\b(compare|combine|cross[- ]?check|synthesize|synthesis)\b.*\b(charts|methods|sources)\b",
        ],
        "contradiction": [
            r"\b(contradict|conflict|clash|opposite|different|difference)\b",
            r"\b(but|however|although|yet)\b.*\b(says|shows|indicates)\b",
        ],
        "deep_timing": [
            r"\b(detailed|comprehensive|precise|exact|pinpoint|specific)\b.*\b(timing|dates|months|years)\b",
            r"\buse\b.*\b(three|four|five|multiple)\b.*\b(methods|texts|systems)\b",
        ],
    }

    _TIMING_HINTS = [
        r"\bwhen\b",
        r"\btiming\b",
        r"\bperiod\b",
        r"\bdate\b",
        r"\bmonth\b",
        r"\byear\b",
        r"\bdasha\b",
        r"\btransit\b",
    ]

    def classify(self, question: str) -> ClassificationResult:
        """Classify question complexity in under a millisecond.

        Parameters
        ----------
        question: str
            User question extracted from the chat interface.
        """

        normalized = question.strip().lower()
        if not normalized:
            return ClassificationResult("SIMPLE", "general", 0.5, "Empty question defaults to SIMPLE")

        # Check for complex patterns first – they should pre-empt simple rules.
        for intent, patterns in self._COMPLEX_PATTERNS.items():
            if any(re.search(pattern, normalized) for pattern in patterns):
                return ClassificationResult("COMPLEX", intent, 0.9, f"Matched complex pattern: {intent}")

        # Simple patterns next – majority traffic should match these.
        for intent, patterns in self._SIMPLE_PATTERNS.items():
            if any(re.search(pattern, normalized) for pattern in patterns):
                return ClassificationResult("SIMPLE", intent, 0.85, f"Matched simple pattern: {intent}")

        # Default to MODERATE when heuristics don't provide a clear answer.
        intent = "timing" if any(re.search(pat, normalized) for pat in self._TIMING_HINTS) else "general"
        return ClassificationResult("MODERATE", intent, 0.7, "Defaulted to MODERATE based on keywords")
