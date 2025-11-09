"""
Simple Chart Parser for Approach B
Parses chart text and extracts basic factors using LLM
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List

from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChartParser:
    """
    Real chart parser for Approach B
    Uses Gemini to extract astrological factors from chart text
    """
    
    def __init__(self):
        """Initialize chart parser with Gemini client"""
        self.project_id = os.getenv("GCP_PROJECT_ID", "superb-analog-464304-s0")
        self.location = os.getenv("GCP_REGION", "asia-south1")
        
        # Initialize Gemini client
        try:
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
            logger.info("Chart parser initialized with Gemini LLM")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}")
            self.client = None
    
    def parse_chart_text(self, chart_data: str, niche: str) -> Dict:
        """
        Parse chart text and extract factors using Gemini LLM
        
        Args:
            chart_data (str): Raw chart data from user
            niche (str): Analysis niche
        
        Returns:
            Dict: Extracted chart factors
        """
        
        logger.info("Parsing chart data with Gemini LLM...")
        
        if not self.client:
            logger.warning("Gemini client not available, using regex fallback")
            return self._fallback_parse(chart_data, niche)
        
        try:
            # Build parsing prompt
            prompt = self._build_parsing_prompt(chart_data, niche)
            
            # Call Gemini to parse the chart
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,  # Deterministic
                    max_output_tokens=2000,
                    response_mime_type="application/json"
                )
            )
            
            # Parse JSON response
            response_text = response.text if hasattr(response, 'text') else None
            
            if not response_text:
                logger.warning("Empty response from Gemini, using fallback")
                return self._fallback_parse(chart_data, niche)
            
            factors = json.loads(response_text)
            factors["parsing_method"] = "gemini_llm"
            factors["chart_source"] = "user_input"
            
            logger.info(f"Parsed {len(factors)} chart factors using Gemini")
            return factors
            
        except Exception as e:
            logger.error(f"Gemini parsing failed: {e}")
            logger.info("Using regex fallback parser")
            return self._fallback_parse(chart_data, niche)
    
    def _build_parsing_prompt(self, chart_data: str, niche: str) -> str:
        """Build prompt for Gemini to parse chart data"""
        
        prompt = f"""
You are an expert Vedic astrology chart parser.

USER'S CHART DATA:
{chart_data}

ANALYSIS NICHE: {niche}

YOUR TASK: Extract ALL astrological factors from the chart data above and return as JSON.

IMPORTANT: 
- Extract ACTUAL values from the user's chart data (including from JSON structures)
- DO NOT make up or assume any values
- If a value is not mentioned, use null
- Be precise with placements (e.g., "7th house", "11th house Taurus")
- For Mahadasha data: Find the current date (November 8, 2025) and determine which period is active
- Also extract all Mahadasha/Antardasha periods within ±20 years (2005-2045)
- Parse D1 chart data to extract planet positions (current_sign, house_number, zodiac_sign_name, nakshatra_name)
- Parse D9 (Navamsa) chart data separately
- Parse D10 (Dasamsa) chart data separately for career analysis

RETURN THIS EXACT JSON STRUCTURE:
{{
  "ascendant": "Cancer or Leo or null",
  "ascendant_lord": "Moon or Sun or null",
  "ascendant_lord_placement": "house and sign",
  "ascendant_sign": "sign name from zodiac_sign_name",
  "ascendant_nakshatra": "nakshatra name",
  
  "7th_house_sign": "sign of 7th house",
  "7th_lord": "planet ruling 7th house",
  "7th_lord_placement": "where 7th lord is placed",
  "planets_in_7th": "planets in 7th house",
  
  "venus_sign": "sign where Venus is",
  "venus_house": "house number where Venus is",
  "venus_nakshatra": "nakshatra of Venus",
  "venus_aspects": "what Venus aspects",
  
  "mars_sign": "sign where Mars is",
  "mars_house": "house number",
  "mars_retrograde": true or false,
  
  "jupiter_sign": "sign where Jupiter is",
  "jupiter_house": "house number",
  "jupiter_retrograde": true or false,
  
  "saturn_sign": "sign where Saturn is",
  "saturn_house": "house number",
  "saturn_retrograde": true or false,
  
  "moon_sign": "sign where Moon is",
  "moon_house": "house number",
  "moon_nakshatra": "nakshatra of Moon",
  
  "sun_sign": "sign where Sun is",
  "sun_house": "house number",
  
  "mercury_sign": "sign where Mercury is",
  "mercury_house": "house number",
  
  "rahu_sign": "sign where Rahu is",
  "rahu_house": "house number",
  
  "ketu_sign": "sign where Ketu is",
  "ketu_house": "house number",
  
  "darakaraka_planet": "planet with 2nd lowest degree",
  "darakaraka_sign": "sign where DK is",
  "darakaraka_house": "house where DK is",
  
  "current_mahadasha": "current major period planet (as of Nov 2025)",
  "current_antardasha": "current sub-period planet (as of Nov 2025)",
  "mahadasha_start_date": "start date of current mahadasha",
  "mahadasha_end_date": "end date of current mahadasha",
  "antardasha_start_date": "start date of current antardasha",
  "antardasha_end_date": "end date of current antardasha",
  
  "d9_ascendant": "Navamsa ascendant sign",
  "d9_7th_house": "Navamsa 7th house sign",
  "d9_7th_lord": "Navamsa 7th lord",
  "d9_venus_sign": "Venus sign in Navamsa",
  "d9_venus_house": "Venus house in Navamsa",
  "d9_moon_sign": "Moon sign in Navamsa",
  "d9_moon_house": "Moon house in Navamsa",
  "d9_jupiter_sign": "Jupiter sign in Navamsa",
  "d9_mars_sign": "Mars sign in Navamsa",
  
  "d10_ascendant": "Dasamsa (D10) ascendant sign for career",
  "d10_10th_house": "D10 10th house sign",
  "d10_sun_sign": "Sun sign in D10",
  "d10_sun_house": "Sun house in D10",
  "d10_saturn_sign": "Saturn sign in D10",
  "d10_saturn_house": "Saturn house in D10",
  "d10_jupiter_sign": "Jupiter sign in D10",
  "d10_jupiter_house": "Jupiter house in D10",
  "d10_mercury_sign": "Mercury sign in D10",
  "d10_venus_sign": "Venus sign in D10",
  
  "d10_ascendant": "Dasamsa ascendant",
  "d10_10th_house": "D10 10th house sign",
  
  "yogas": ["list of yogas present"],
  "special_combinations": ["any special combinations"],
  
  "chart_strength": "strong/moderate/weak",
  "benefic_planets": ["list of benefic planets for this chart"],
  "malefic_planets": ["list of malefic planets for this chart"]
}}

STRICTLY RETURN ONLY VALID JSON. Extract from the actual chart data provided.
"""
        
        return prompt
    
    def _extract_json_objects(self, text: str) -> List[Dict]:
        """Extract all valid JSON objects from text by finding balanced braces"""
        results = []
        depth = 0
        start = None
        in_string = False
        escape = False
        
        for i, char in enumerate(text):
            if escape:
                escape = False
                continue
                
            if char == '\\':
                escape = True
                continue
                
            if char == '"' and not escape:
                in_string = not in_string
                continue
                
            if in_string:
                continue
                
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    json_str = text[start:i+1]
                    try:
                        obj = json.loads(json_str)
                        results.append(obj)
                        logger.debug(f"Found valid JSON object at position {start}")
                    except Exception as e:
                        logger.debug(f"Invalid JSON at position {start}: {str(e)[:100]}")
                    start = None
        
        return results
    
    def _fallback_parse(self, chart_data: str, niche: str) -> Dict:
        """
        Fallback regex-based parser when LLM is unavailable
        Handles both text and JSON chart data
        """
        
        logger.info("Using regex-based fallback parser")
        
        factors = {}
        
        # Try to parse as JSON first
        try:
            # Extract JSON objects from the chart data
            json_blocks = self._extract_json_objects(chart_data)
            
            for data in json_blocks:
                # data is already a parsed dict from _extract_json_objects
                try:
                    # Parse D1 chart data
                    if "output" in data and isinstance(data["output"], dict):
                        output = data["output"]
                        
                        # Parse Ascendant
                        if "Ascendant" in output:
                            asc = output["Ascendant"]
                            factors["ascendant"] = asc.get("zodiac_sign_name")
                            factors["ascendant_sign"] = asc.get("zodiac_sign_name")
                            factors["ascendant_nakshatra"] = asc.get("nakshatra_name")
                            factors["ascendant_house"] = asc.get("house_number")
                        
                        # Parse planets
                        planet_map = {
                            "Sun": "sun", "Moon": "moon", "Mars": "mars",
                            "Mercury": "mercury", "Jupiter": "jupiter", "Venus": "venus",
                            "Saturn": "saturn", "Rahu": "rahu", "Ketu": "ketu"
                        }
                        
                        for planet_key, planet_name in planet_map.items():
                            if planet_key in output:
                                planet_data = output[planet_key]
                                factors[f"{planet_name}_sign"] = planet_data.get("zodiac_sign_name")
                                factors[f"{planet_name}_house"] = planet_data.get("house_number")
                                factors[f"{planet_name}_nakshatra"] = planet_data.get("nakshatra_name")
                                
                                # Check retrograde
                                if planet_data.get("isRetro") == "true":
                                    factors[f"{planet_name}_retrograde"] = True
                        
                        # Parse D9 chart (Navamsa)
                        # D9 data structure: numbered keys with name, current_sign, house_number
                        if isinstance(output, dict) and "0" in output:
                            # Check if this is D9, D10, or other divisional chart
                            # We need to determine chart type from context or ascendant sign
                            first_planet = output.get("0", {})
                            
                            # Heuristic: if we already have d9_ascendant, this might be d10
                            is_d10 = "d9_ascendant" in factors
                            chart_prefix = "d10" if is_d10 else "d9"
                            
                            for key, planet_data in output.items():
                                if isinstance(planet_data, dict) and "name" in planet_data:
                                    planet_name = planet_data["name"].lower()
                                    if planet_name == "ascendant":
                                        factors[f"{chart_prefix}_ascendant"] = self._get_sign_name(planet_data.get("current_sign"))
                                    else:
                                        factors[f"{chart_prefix}_{planet_name}_sign"] = self._get_sign_name(planet_data.get("current_sign"))
                                        factors[f"{chart_prefix}_{planet_name}_house"] = planet_data.get("house_number")
                                        if planet_data.get("isRetro") == "true":
                                            factors[f"{chart_prefix}_{planet_name}_retrograde"] = True
                    
                    # Parse Mahadasha data
                    # Format: nested dict with planet names as keys and sub-periods
                    if isinstance(data, dict):
                        # Check if this looks like mahadasha data
                        dasha_planets = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
                        if any(planet in data for planet in dasha_planets):
                            # This is mahadasha data - find current period
                            current_date = datetime.now()
                            
                            for maha_planet, antardashas in data.items():
                                if not isinstance(antardashas, dict):
                                    continue
                                    
                                for antar_planet, period in antardashas.items():
                                    if isinstance(period, dict) and "start_time" in period and "end_time" in period:
                                        try:
                                            start = datetime.strptime(period["start_time"], "%Y-%m-%d %H:%M:%S")
                                            end = datetime.strptime(period["end_time"], "%Y-%m-%d %H:%M:%S")
                                            
                                            if start <= current_date <= end:
                                                factors["current_mahadasha"] = maha_planet
                                                factors["current_antardasha"] = antar_planet
                                                factors["mahadasha_start_date"] = period["start_time"]
                                                factors["mahadasha_end_date"] = period["end_time"]
                                                logger.info(f"Found current dasha: {maha_planet}-{antar_planet}")
                                                break
                                        except ValueError:
                                            continue
                                
                                if "current_mahadasha" in factors:
                                    break
                        
                        # Also check for nested "output" key with string value (Mahadasha data)
                        if "output" in data and isinstance(data["output"], str):
                            try:
                                nested_data = json.loads(data["output"])
                                # Recursively parse nested data
                                if isinstance(nested_data, dict):
                                    current_date = datetime.now()
                                    
                                    # Lists to store dasha periods
                                    all_periods = []
                                    
                                    # Extract all periods first
                                    for maha_planet, antardashas in nested_data.items():
                                        if not isinstance(antardashas, dict):
                                            continue
                                        for antar_planet, period in antardashas.items():
                                            if isinstance(period, dict) and "start_time" in period and "end_time" in period:
                                                try:
                                                    start = datetime.strptime(period["start_time"], "%Y-%m-%d %H:%M:%S")
                                                    end = datetime.strptime(period["end_time"], "%Y-%m-%d %H:%M:%S")
                                                    
                                                    all_periods.append({
                                                        "maha": maha_planet,
                                                        "antar": antar_planet,
                                                        "start": start,
                                                        "end": end,
                                                        "start_str": period["start_time"],
                                                        "end_str": period["end_time"]
                                                    })
                                                except ValueError:
                                                    continue
                                    
                                    # Sort periods by start date
                                    all_periods.sort(key=lambda x: x["start"])
                                    
                                    # Find current period and periods within ±20 years
                                    twenty_years_ago = current_date.replace(year=current_date.year - 20)
                                    twenty_years_future = current_date.replace(year=current_date.year + 20)
                                    
                                    relevant_periods = []
                                    current_period = None
                                    
                                    for period in all_periods:
                                        # Check if this is the current period
                                        if period["start"] <= current_date <= period["end"]:
                                            current_period = period
                                            factors["current_mahadasha"] = period["maha"]
                                            factors["current_antardasha"] = period["antar"]
                                            factors["antardasha_start_date"] = period["start_str"]
                                            factors["antardasha_end_date"] = period["end_str"]
                                            logger.info(f"Found current dasha: {period['maha']}-{period['antar']}")
                                        
                                        # Check if period overlaps with ±20 year window
                                        if (period["end"] >= twenty_years_ago and period["start"] <= twenty_years_future):
                                            relevant_periods.append({
                                                "mahadasha": period["maha"],
                                                "antardasha": period["antar"],
                                                "start_date": period["start_str"],
                                                "end_date": period["end_str"],
                                                "is_current": (period == current_period)
                                            })
                                    
                                    # Store all relevant periods
                                    if relevant_periods:
                                        factors["dasha_periods_20yr"] = relevant_periods
                                        factors["total_periods_20yr"] = len(relevant_periods)
                                        logger.info(f"Stored {len(relevant_periods)} dasha periods (±20 years)")
                                        
                            except json.JSONDecodeError:
                                pass
                
                except json.JSONDecodeError:
                    continue
        
        except Exception as e:
            logger.warning(f"Error parsing JSON: {e}")
        
        # Fallback to regex parsing if JSON parsing didn't work
        chart_lower = chart_data.lower()
        
        if not factors.get("ascendant"):
            # Extract Ascendant
            asc_match = re.search(r'ascendant[:\s]+(\w+)', chart_lower, re.IGNORECASE)
            if asc_match:
                factors["ascendant"] = asc_match.group(1).title()
        
        if not factors.get("7th_house_sign"):
            # Extract 7th house info
            seventh_match = re.search(r'7th\s+house[:\s]+(\w+)', chart_lower, re.IGNORECASE)
            if seventh_match:
                factors["7th_house_sign"] = seventh_match.group(1).title()
        
        # Extract Dasha if not already found
        if not factors.get("current_mahadasha"):
            dasha_match = re.search(r'dasha[:\s]+(\w+)-(\w+)', chart_lower, re.IGNORECASE)
            if dasha_match:
                factors["current_mahadasha"] = dasha_match.group(1).title()
                factors["current_antardasha"] = dasha_match.group(2).title()
            elif re.search(r'dasha[:\s]+(\w+)', chart_lower, re.IGNORECASE):
                dasha_single = re.search(r'dasha[:\s]+(\w+)', chart_lower, re.IGNORECASE)
                factors["current_mahadasha"] = dasha_single.group(1).title()
        
        if not factors.get("d9_ascendant"):
            # Extract Navamsa (D9) info
            d9_match = re.search(r'd9.*?ascendant[:\s]+(\w+)', chart_lower, re.IGNORECASE)
            if d9_match:
                factors["d9_ascendant"] = d9_match.group(1).title()
        
        # Add metadata
        factors["parsing_method"] = "regex_fallback"
        factors["chart_source"] = "user_input"
        factors["has_real_data"] = len(factors) > 2
        
        logger.info(f"Parsed {len(factors)} factors using regex fallback")
        return factors
    
    def _get_sign_name(self, sign_number: int) -> str:
        """Convert sign number to sign name"""
        signs = {
            1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
            5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
            9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
        }
        return signs.get(sign_number, f"Sign_{sign_number}")
