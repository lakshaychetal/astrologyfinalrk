"""
Niche-Specific Configuration
Maps each astrology niche to its relevant chart factors and divisional charts
Professional-grade configuration for intelligent pre-loading
"""

from datetime import timedelta
from typing import Dict, List, Any

# ===== NICHE-SPECIFIC FACTOR MAPPINGS =====

NICHE_FACTOR_MAP: Dict[str, Dict[str, Any]] = {
    "Love & Relationships": {
        "description": "Marriage, spouse, relationships, romance",
        
        # D1 (Rasi) Chart Factors - EXPANDED FOR BEST QUALITY
        "d1_factors": [
            # Venus - primary love significator (EXPANDED)
            "venus_sign", "venus_house", "venus_nakshatra", "venus_pada", 
            "venus_degree", "venus_retrograde", "venus_combustion",
            "venus_aspects", "venus_conjunction", "venus_strength",
            "venus_dignity", "venus_navamsa_placement",
            
            # 7th House - marriage & partnership (EXPANDED)
            "7th_house_sign", "7th_lord", "7th_lord_placement", "7th_lord_house",
            "7th_lord_sign", "7th_lord_nakshatra", "7th_lord_retrograde",
            "7th_lord_strength", "7th_lord_dignity", "7th_lord_aspects",
            "planets_in_7th", "7th_house_aspects", "7th_house_malefics",
            "7th_house_benefics", "7th_cusp_degree",
            
            # 5th House - romance & attraction (EXPANDED)
            "5th_house_sign", "5th_lord", "5th_lord_placement", "5th_lord_house",
            "5th_lord_sign", "planets_in_5th", "5th_house_aspects",
            "5th_lord_strength", "5th_house_benefics",
            
            # 8th House - intimacy & transformation (NEW)
            "8th_house_sign", "8th_lord", "8th_lord_placement", "8th_lord_house",
            "planets_in_8th", "8th_house_mars", "8th_house_venus",
            
            # 2nd House - family acceptance (NEW)
            "2nd_house_sign", "2nd_lord", "2nd_lord_placement",
            "planets_in_2nd", "2nd_house_benefics",
            
            # 11th House - social circles, gains from spouse (NEW)
            "11th_house_sign", "11th_lord", "11th_lord_placement",
            "planets_in_11th", "11th_house_venus", "11th_house_jupiter",
            
            # Darakaraka - spouse indicator (EXPANDED)
            "darakaraka_planet", "darakaraka_sign", "darakaraka_house",
            "darakaraka_nakshatra", "darakaraka_strength", "darakaraka_dignity",
            "darakaraka_aspects", "darakaraka_conjunction",
            
            # Supporting planets (EXPANDED)
            "moon_sign", "moon_house", "moon_nakshatra", "moon_pada",
            "moon_degree", "moon_aspects", "moon_strength",  # Emotional nature
            
            "mars_sign", "mars_house", "mars_nakshatra",  # Passion, conflict
            "mars_aspects", "mars_strength", "mars_manglik_check",
            
            "jupiter_sign", "jupiter_house", "jupiter_nakshatra",  # Blessings
            "jupiter_aspects", "jupiter_strength", "jupiter_dignity",
            
            "saturn_sign", "saturn_house", "saturn_nakshatra",  # Delays, karma
            "saturn_7th_aspect", "saturn_influence_venus",
            
            "rahu_sign", "rahu_house", "rahu_nakshatra",  # Unconventional
            "rahu_7th_influence", "rahu_venus_conjunction",
            
            "ketu_sign", "ketu_house", "ketu_nakshatra",  # Spiritual bond
            
            # Ascendant - overall personality (EXPANDED)
            "ascendant_sign", "ascendant_nakshatra", "ascendant_degree",
            "ascendant_lord", "ascendant_lord_placement", "ascendant_lord_strength",
            
            # Special indicators (EXPANDED)
            "upapada_lagna", "upapada_lord", "upapada_planets",
            "arudha_pada_a7", "karakamsa_lagna",
            
            # Yogas & combinations (NEW)
            "graha_malika_yoga", "parivartan_yoga", "rajayoga_7th",
            "chandra_mangala_yoga", "mahapurusha_yoga",
            "venus_jupiter_combination", "moon_venus_combination",
        ],
        
        # D9 (Navamsa) Chart - marriage quality (EXPANDED FOR BEST QUALITY)
        "d9_factors": [
            # Core D9 factors
            "d9_ascendant", "d9_ascendant_lord", "d9_ascendant_strength",
            
            # Venus in D9 (EXPANDED)
            "d9_venus", "d9_venus_sign", "d9_venus_house",
            "d9_venus_nakshatra", "d9_venus_strength", "d9_venus_dignity",
            "d9_venus_aspects", "d9_venus_conjunction",
            
            # 7th house in D9 (EXPANDED)
            "d9_7th_house", "d9_7th_lord", "d9_7th_lord_placement",
            "d9_7th_lord_strength", "d9_7th_house_planets",
            "d9_7th_lord_aspects", "d9_7th_house_benefics",
            
            # Planets in D9 (EXPANDED)
            "d9_moon", "d9_moon_sign", "d9_moon_house", "d9_moon_strength",
            "d9_mars", "d9_mars_sign", "d9_mars_house", "d9_mars_strength",
            "d9_jupiter", "d9_jupiter_sign", "d9_jupiter_strength",
            "d9_saturn", "d9_saturn_sign", "d9_saturn_influence",
            "d9_rahu", "d9_ketu", "d9_sun", "d9_mercury",
            
            # D9 special factors (NEW)
            "d9_darakaraka", "d9_darakaraka_placement",
            "d9_upapada", "d9_karakamsa",
            "d9_navamsa_strength_overall", "d9_vargottama_planets",
            "d9_pushkara_navamsa", "d9_planetary_dignity",
            
            # D9 yogas (NEW)
            "d9_rajayoga", "d9_dhana_yoga", "d9_neecha_bhanga",
        ],
        
        # D7 (Saptamsa) - Children & progeny (NEW)
        "d7_factors": [
            "d7_5th_house", "d7_5th_lord", "d7_jupiter",
            "d7_moon", "d7_children_potential",
        ],
        
        # Dashas - timing of marriage/relationships
        "dasha_config": {
            "default_range": "±5 years",  # For general timing questions
            "extended_range": "±20 years",  # For life overview
            "focus_periods": ["Venus", "Jupiter", "7th_lord", "Darakaraka", "Moon", "Rahu"],
            
            # TIMING INTELLIGENCE: Auto-query Vimshottari Dashas for "when" questions
            "timing_factors": [
                # Venus Dasha Periods (Primary Marriage Significator)
                "venus_mahadasha_timing", "venus_antardasha_timing", "venus_pratyantar_timing",
                "venus_mahadasha_strength", "venus_antardasha_effects", "venus_sub_periods",
                "venus_dasha_marriage_yoga", "venus_dasha_activation",
                
                # Jupiter Dasha Periods (Blessings, Expansion)
                "jupiter_mahadasha_timing", "jupiter_antardasha_timing", "jupiter_pratyantar_timing",
                "jupiter_mahadasha_effects", "jupiter_antardasha_marriage", "jupiter_transit_marriage",
                "jupiter_dasha_blessings", "jupiter_return_timing",
                
                # 7th Lord Dasha Periods
                "7th_lord_mahadasha", "7th_lord_antardasha", "7th_lord_pratyantar",
                "7th_lord_dasha_strength", "7th_lord_dasha_effects", "7th_lord_activation_timing",
                
                # Moon Dasha Periods (Emotional Readiness)
                "moon_mahadasha_effects", "moon_antardasha_effects", "moon_pratyantar_timing",
                "moon_dasha_emotional_state", "moon_dasha_relationship_readiness",
                
                # Rahu/Ketu Dasha Periods (Sudden Meetings, Karma)
                "rahu_mahadasha_marriage", "rahu_antardasha_marriage", "rahu_pratyantar_timing",
                "ketu_mahadasha_effects", "ketu_antardasha_effects", "rahu_ketu_axis_timing",
                "rahu_dasha_sudden_meetings", "ketu_dasha_spiritual_connections",
                
                # Darakaraka Dasha Periods
                "darakaraka_dasha_period", "darakaraka_mahadasha_effects", "darakaraka_antardasha",
                "darakaraka_activation_timing", "darakaraka_dasha_strength",
                
                # 5th Lord Dasha Periods (Romance, Love Affairs)
                "5th_lord_mahadasha", "5th_lord_antardasha", "5th_lord_dasha_romance",
                
                # Mars Dasha Periods (Passion, Action)
                "mars_mahadasha_effects", "mars_antardasha_timing", "mars_dasha_passion",
                
                # Mercury Dasha Periods (Communication)
                "mercury_mahadasha_effects", "mercury_antardasha_timing", "mercury_dasha_communication",
                
                # Saturn Dasha Periods (Delays, Maturity)
                "saturn_mahadasha_marriage", "saturn_antardasha_effects", "saturn_delay_analysis",
                "saturn_dasha_timing_blocks", "saturn_maturity_timing",
                
                # Sun Dasha Periods (Authority, Status)
                "sun_mahadasha_effects", "sun_antardasha_timing", "sun_dasha_status_marriage",
                
                # Major Transits (Gochara)
                "jupiter_transit_7th_house", "jupiter_transit_venus", "jupiter_transit_moon",
                "saturn_transit_7th_house", "saturn_transit_venus", "saturn_transit_ascendant",
                "rahu_transit_7th_house", "ketu_transit_7th_house", "rahu_ketu_axis_transit",
                "venus_transit_analysis", "venus_return_timing",
                
                # Double Transits (Sarvastaka Varga)
                "jupiter_saturn_double_transit", "jupiter_rahu_double_transit",
                "saturn_venus_double_transit", "double_transit_marriage_axis",
                
                # Marriage Timing Combinations
                "marriage_timing_combinations", "marriage_yoga_activation_period",
                "dasha_sandhi_marriage", "dasha_transition_marriage_timing",
                "sub_sub_dasha_activation", "specific_month_predictions",
                
                # Current Dasha Analysis
                "current_mahadasha_analysis", "current_antardasha_analysis",
                "upcoming_dasha_sequence", "next_5_years_dasha_periods",
                "life_timeline_marriage_windows", "best_marriage_periods_ranking",
            ],
        },
        
        # Divisional charts to analyze
        "divisional_charts": ["D1", "D9", "D7"],  # D1 (Rashi), D9 (Navamsa), D7 (Saptamsa)
        
        # Total expected factors (60 D1 + 40 D9 + 5 D7 + 85 timing = 190 total)
        "total_factors": 190,
        
        # Pre-loading priority
        "priority": "highest",  # Critical for quality timing predictions
        
        # Cache TTL (Time To Live)
        "cache_ttl_minutes": 120,  # 2 hours
    },
    
    "Career & Finance": {
        "description": "Career path, profession, income, wealth",
        
        "d1_factors": [
            # 10th House - career & profession
            "10th_house_sign", "10th_lord", "10th_lord_placement", "10th_lord_house",
            "10th_lord_sign", "10th_lord_nakshatra", "10th_lord_retrograde",
            "planets_in_10th",
            
            # Sun - authority, career status
            "sun_sign", "sun_house", "sun_nakshatra", "sun_degree",
            
            # Saturn - hard work, discipline
            "saturn_sign", "saturn_house", "saturn_nakshatra", "saturn_retrograde",
            
            # Jupiter - expansion, wisdom
            "jupiter_sign", "jupiter_house", "jupiter_nakshatra", "jupiter_retrograde",
            
            # 2nd House - wealth, income
            "2nd_house_sign", "2nd_lord", "2nd_lord_placement", "planets_in_2nd",
            
            # 6th House - service, competition
            "6th_house_sign", "6th_lord", "6th_lord_placement", "planets_in_6th",
            
            # 11th House - gains, income
            "11th_house_sign", "11th_lord", "11th_lord_placement", "planets_in_11th",
            
            # Atmakaraka - soul purpose
            "atmakaraka_planet", "atmakaraka_sign", "atmakaraka_house",
            
            # Ascendant
            "ascendant_sign", "ascendant_lord",
            
            # Moon - mind, emotions at work
            "moon_sign", "moon_house",
        ],
        
        "d9_factors": [
            "d9_10th_house", "d9_10th_lord",
            "d9_sun", "d9_saturn",
        ],
        
        "d10_factors": [  # Dasamsa - specific for career
            "d10_ascendant", "d10_ascendant_lord",
            "d10_10th_house", "d10_10th_lord",
            "d10_sun", "d10_saturn", "d10_jupiter",
        ],
        
        "dasha_config": {
            "default_range": "±5 years",
            "extended_range": "±20 years",
            "focus_periods": ["Sun", "Saturn", "Jupiter", "10th_lord"],
        },
        
        "divisional_charts": ["D1", "D9", "D10"],
        "total_factors": 48,
        "priority": "high",
        "cache_ttl_minutes": 120,
    },
    
    "Health & Wellness": {
        "description": "Health issues, disease, vitality, longevity",
        
        "d1_factors": [
            # Ascendant - physical body
            "ascendant_sign", "ascendant_lord", "ascendant_nakshatra",
            
            # 6th House - disease, health issues
            "6th_house_sign", "6th_lord", "6th_lord_placement", "planets_in_6th",
            
            # 8th House - chronic illness, surgery
            "8th_house_sign", "8th_lord", "8th_lord_placement", "planets_in_8th",
            
            # 12th House - hospitalization, losses
            "12th_house_sign", "12th_lord", "12th_lord_placement", "planets_in_12th",
            
            # Mars - energy, injuries, surgery
            "mars_sign", "mars_house", "mars_nakshatra",
            
            # Saturn - chronic issues, bones
            "saturn_sign", "saturn_house", "saturn_nakshatra", "saturn_retrograde",
            
            # Moon - mental health, fluids
            "moon_sign", "moon_house", "moon_nakshatra",
            
            # Sun - vitality, heart, father
            "sun_sign", "sun_house", "sun_nakshatra",
            
            # Jupiter - healing, liver
            "jupiter_sign", "jupiter_house",
        ],
        
        "d9_factors": [
            "d9_ascendant", "d9_6th_house", "d9_8th_house",
        ],
        
        "dasha_config": {
            "default_range": "±3 years",  # Health changes faster
            "extended_range": "±10 years",
            "focus_periods": ["Mars", "Saturn", "6th_lord", "8th_lord"],
        },
        
        "divisional_charts": ["D1", "D3", "D9"],  # D3 for siblings/health
        "total_factors": 35,
        "priority": "medium",
        "cache_ttl_minutes": 90,
    },
    
    "Spiritual & Education": {
        "description": "Spirituality, higher learning, dharma, fortune",
        
        "d1_factors": [
            # 9th House - dharma, higher learning, fortune
            "9th_house_sign", "9th_lord", "9th_lord_placement", "planets_in_9th",
            
            # 12th House - spirituality, moksha
            "12th_house_sign", "12th_lord", "12th_lord_placement", "planets_in_12th",
            
            # Jupiter - guru, wisdom, dharma
            "jupiter_sign", "jupiter_house", "jupiter_nakshatra", "jupiter_retrograde",
            
            # Ketu - spirituality, detachment
            "ketu_sign", "ketu_house", "ketu_nakshatra",
            
            # 5th House - intelligence, past life credit
            "5th_house_sign", "5th_lord", "planets_in_5th",
            
            # Moon - mind, meditation
            "moon_sign", "moon_house", "moon_nakshatra",
            
            # Ascendant
            "ascendant_sign", "ascendant_nakshatra",
        ],
        
        "d9_factors": [
            "d9_ascendant", "d9_jupiter", "d9_ketu",
            "d9_9th_house", "d9_12th_house",
        ],
        
        "dasha_config": {
            "default_range": "±5 years",
            "extended_range": "±20 years",
            "focus_periods": ["Jupiter", "Ketu", "9th_lord"],
        },
        
        "divisional_charts": ["D1", "D9", "D20"],  # D20 for spiritual progress
        "total_factors": 32,
        "priority": "medium",
        "cache_ttl_minutes": 90,
    },
}


# ===== SMART DASHA EXTRACTION RULES =====

DASHA_EXTRACTION_RULES = {
    "timing_keywords": {
        "keywords": ["when", "timing", "soon", "next", "year", "months", "date"],
        "range": "±5 years",
        "description": "Near-term timing questions"
    },
    
    "past_keywords": {
        "keywords": ["was", "did", "happened", "ago", "before", "past", "previously"],
        "range": "±20 years (past focus)",
        "description": "Past event analysis"
    },
    
    "future_keywords": {
        "keywords": ["will", "future", "going to", "later", "eventually", "someday"],
        "range": "±20 years (future focus)",
        "description": "Long-term predictions"
    },
    
    "current_keywords": {
        "keywords": ["now", "currently", "present", "today", "this year"],
        "range": "±2 years",
        "description": "Current period only"
    },
}


# ===== CACHE CONFIGURATION =====

CACHE_CONFIG = {
    "enabled": True,
    "type": "redis",  # Options: "redis", "memory", "none"
    
    # Redis connection
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": None,  # Set if Redis requires auth
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "decode_responses": True,
    },
    
    # Cache keys structure
    "key_format": "astro:rag:{session_id}:{niche}:{factor}",
    
    # TTL settings
    "default_ttl_minutes": 60,  # 1 hour default
    "session_ttl_minutes": 180,  # 3 hours for session data
    
    # Pre-loading settings (OPTIMIZED FOR PARALLEL RETRIEVAL)
    "preload": {
        "batch_size": 10,  # Process 10 factors at once (increased from 5)
        "max_parallel": 10,  # Max parallel RAG queries (increased from 4)
        "timeout_seconds": 180,  # 3 minutes max for pre-loading (increased)
        "retry_attempts": 2,
    },
    
    # Cache hit tracking
    "track_hits": True,
    "hit_threshold": 0.80,  # 80% cache hit rate target
}


# ===== HELPER FUNCTIONS =====

def get_niche_factors(niche: str) -> List[str]:
    """
    Get all factor names for a specific niche (including D1, D9, D7, and timing factors)
    
    Args:
        niche: Niche name (e.g., "Love & Relationships")
    
    Returns:
        List of all factor names (190+ for Love & Relationships)
    """
    config = NICHE_FACTOR_MAP.get(niche, {})
    
    all_factors = []
    all_factors.extend(config.get("d1_factors", []))
    all_factors.extend(config.get("d9_factors", []))
    all_factors.extend(config.get("d7_factors", []))  # Added D7
    all_factors.extend(config.get("d10_factors", []))
    
    # Add timing factors from dasha_config
    dasha_config = config.get("dasha_config", {})
    all_factors.extend(dasha_config.get("timing_factors", []))
    
    return all_factors


def get_dasha_range(question: str, niche: str) -> Dict[str, Any]:
    """
    Determine intelligent dasha extraction range based on question
    
    Args:
        question: User's question
        niche: Selected niche
    
    Returns:
        Dict with range info
    """
    question_lower = question.lower()
    
    # Check for timing keywords
    for rule_name, rule in DASHA_EXTRACTION_RULES.items():
        if any(kw in question_lower for kw in rule["keywords"]):
            return {
                "range": rule["range"],
                "description": rule["description"],
                "rule": rule_name
            }
    
    # Default to niche configuration
    niche_config = NICHE_FACTOR_MAP.get(niche, {})
    default_range = niche_config.get("dasha_config", {}).get("default_range", "±5 years")
    
    return {
        "range": default_range,
        "description": "Default niche range",
        "rule": "niche_default"
    }


def get_cache_ttl(niche: str) -> int:
    """
    Get cache TTL (in seconds) for a niche
    
    Args:
        niche: Niche name
    
    Returns:
        TTL in seconds
    """
    niche_config = NICHE_FACTOR_MAP.get(niche, {})
    ttl_minutes = niche_config.get("cache_ttl_minutes", CACHE_CONFIG["default_ttl_minutes"])
    return ttl_minutes * 60


def should_use_extended_dasha(question: str) -> bool:
    """
    Determine if extended dasha range (±20 years) should be used
    
    Args:
        question: User's question
    
    Returns:
        True if extended range needed
    """
    extended_keywords = [
        "life", "lifetime", "entire", "all", "complete", "full",
        "overview", "history", "timeline", "journey"
    ]
    
    return any(kw in question.lower() for kw in extended_keywords)


def is_timing_question(question: str) -> bool:
    """
    Detect if the question is asking about timing
    
    Args:
        question: User's question
    
    Returns:
        True if it's a timing question
    """
    timing_keywords = [
        "when", "timing", "time", "period", "year", "age",
        "soon", "later", "future", "upcoming", "next",
        "current", "now", "this year", "how long",
        "dasha", "mahadasha", "antardasha", "transit"
    ]
    
    return any(kw in question.lower() for kw in timing_keywords)


def get_timing_factors(niche: str, chart_factors: Dict[str, Any] = None) -> List[str]:
    """
    Get relevant timing factors (Vimshottari Dashas) for a niche
    Intelligently extracts which planetary periods are important
    
    Args:
        niche: Astrology niche
        chart_factors: Parsed chart factors (optional, to find 7th lord etc.)
    
    Returns:
        List of timing factor names to query
    """
    niche_config = NICHE_FACTOR_MAP.get(niche, {})
    dasha_config = niche_config.get("dasha_config", {})
    
    # Get base timing factors from config
    timing_factors = dasha_config.get("timing_factors", [])
    
    # If chart factors provided, add specific planet dashas
    if chart_factors and niche == "Love & Relationships":
        # Find 7th lord
        seventh_lord = chart_factors.get("7th_lord", "")
        if seventh_lord:
            timing_factors.extend([
                f"{seventh_lord.lower()}_mahadasha_marriage",
                f"{seventh_lord.lower()}_antardasha_timing"
            ])
        
        # Find darakaraka
        darakaraka = chart_factors.get("darakaraka_planet", "")
        if darakaraka:
            timing_factors.extend([
                f"{darakaraka.lower()}_dasha_spouse",
                f"{darakaraka.lower()}_period_relationship"
            ])
    
    return timing_factors


def get_all_factors_with_timing(niche: str, question: str, chart_factors: Dict[str, Any] = None) -> List[str]:
    """
    Get all relevant factors including timing factors if question asks "when"
    
    Args:
        niche: Astrology niche
        question: User's question
        chart_factors: Parsed chart factors
    
    Returns:
        Combined list of regular + timing factors
    """
    # Get base factors
    base_factors = get_niche_factors(niche)
    
    # If timing question, add timing factors
    if is_timing_question(question):
        timing_factors = get_timing_factors(niche, chart_factors)
        # Combine and deduplicate
        all_factors = list(set(base_factors + timing_factors))
        return all_factors
    
    return base_factors
