"""
Niche Instructions Module - Contains specialized system instructions for different astrology domains
"""

from .love import LOVE_INSTRUCTION
from .career import CAREER_INSTRUCTION
from .wealth import WEALTH_INSTRUCTION
from .health import HEALTH_INSTRUCTION
from .spiritual import SPIRITUAL_INSTRUCTION

# Dictionary mapping niche names to their system instructions
NICHE_INSTRUCTIONS = {
    "Love & Relationships": LOVE_INSTRUCTION,
    "Career & Professional": CAREER_INSTRUCTION,
    "Wealth & Finance": WEALTH_INSTRUCTION,
    "Health & Wellness": HEALTH_INSTRUCTION,
    "Spiritual Purpose": SPIRITUAL_INSTRUCTION
}

# List for UI display order with emojis (label, value) tuples for Gradio Radio
NICHE_CHOICES = [
    ("💕 Love & Relationships", "Love & Relationships"),
    ("💼 Career & Professional", "Career & Professional"),
    ("💰 Wealth & Finance", "Wealth & Finance"),
    ("🏥 Health & Wellness", "Health & Wellness"),
    ("🧘 Spiritual Purpose", "Spiritual Purpose")
]

__all__ = [
    'LOVE_INSTRUCTION',
    'CAREER_INSTRUCTION',
    'WEALTH_INSTRUCTION',
    'HEALTH_INSTRUCTION',
    'SPIRITUAL_INSTRUCTION',
    'NICHE_INSTRUCTIONS',
    'NICHE_CHOICES'
]
