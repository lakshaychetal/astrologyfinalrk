import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
    SentenceTransformer = None

try:
    import swisseph as swe  # type: ignore
except Exception:
    swe = None

from database import db

logger = logging.getLogger(__name__)


class AstrologyService:
    def __init__(self, api_key: str | None = None, base_url: str = "https://json.freeastrologyapi.com"):
        # read from environment via config if not provided
        import os
        self.api_key = api_key or os.getenv("ASTROLOGY_API_KEY")
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self.headers["x-api-key"] = self.api_key

    def parse_api_response(self, api_responses: Dict[str, Any]) -> List[str]:
        snippets: List[str] = []
        logger.info(f"Parsing API responses: {list(api_responses.keys())}")

        # planets
        if "planets" in api_responses:
            planets_data = api_responses["planets"]
            logger.debug(f"Planets API response: {json.dumps(planets_data, indent=2)}")
            if isinstance(planets_data, dict) and "output" in planets_data:
                for planet in planets_data["output"]:
                    if isinstance(planet, dict):
                        name = planet.get("planet", "")
                        sign = planet.get("sign", "")
                        house = planet.get("house", "")
                        degree = planet.get("fullDegree", "")
                        if name and sign and house:
                            snippets.append(f"{name} is positioned in {sign} sign in the {house} house at {degree} degrees")
                        elif name and sign:
                            snippets.append(f"{name} is in {sign} sign")
                    else:
                        try:
                            parsed = json.loads(planet)
                            if isinstance(parsed, dict):
                                name = parsed.get("planet", "")
                                sign = parsed.get("sign", "")
                                house = parsed.get("house", "")
                                degree = parsed.get("fullDegree", "")
                                if name and sign and house:
                                    snippets.append(f"{name} is positioned in {sign} sign in the {house} house at {degree} degrees")
                                elif name and sign:
                                    snippets.append(f"{name} is in {sign} sign")
                            else:
                                snippets.append(str(parsed))
                        except Exception:
                            snippets.append(str(planet))

        # planets extended
        if "planets_extended" in api_responses:
            extended = api_responses["planets_extended"]
            logger.debug(f"Extended planets: {json.dumps(extended, indent=2)}")
            if isinstance(extended, dict) and "output" in extended:
                for planet in extended["output"]:
                    if isinstance(planet, dict):
                        name = planet.get("planet", "")
                        nakshatra = planet.get("nakshatra", "")
                        pada = planet.get("nakshatraPada", "")
                        if name and nakshatra:
                            snippets.append(f"{name} is in {nakshatra} nakshatra, pada {pada}")
                    else:
                        try:
                            parsed = json.loads(planet)
                            if isinstance(parsed, dict):
                                name = parsed.get("planet", "")
                                nakshatra = parsed.get("nakshatra", "")
                                pada = parsed.get("nakshatraPada", "")
                                if name and nakshatra:
                                    snippets.append(f"{name} is in {nakshatra} nakshatra, pada {pada}")
                            else:
                                snippets.append(str(parsed))
                        except Exception:
                            snippets.append(str(planet))

        # transits
        if "transits" in api_responses:
            transits_data = api_responses["transits"]
            logger.debug(f"Transits API response: {json.dumps(transits_data, indent=2)}")
            candidates = []
            if isinstance(transits_data, dict):
                if "output" in transits_data and isinstance(transits_data["output"], list):
                    candidates = transits_data["output"]
                elif "transits" in transits_data and isinstance(transits_data["transits"], list):
                    candidates = transits_data["transits"]
                elif isinstance(transits_data.get("events"), list):
                    candidates = transits_data.get("events", [])

            if isinstance(candidates, list) and candidates:
                for ev in candidates:
                    ev_obj = None
                    if isinstance(ev, dict):
                        ev_obj = ev
                    else:
                        try:
                            parsed = json.loads(ev)
                            if isinstance(parsed, dict):
                                ev_obj = parsed
                            else:
                                snippets.append(str(parsed))
                                continue
                        except Exception:
                            snippets.append(str(ev))
                            continue

                    if not ev_obj:
                        continue

                    planet = ev_obj.get("planet") or ev_obj.get("transiting_planet") or ev_obj.get("body")
                    aspect = ev_obj.get("aspect") or ev_obj.get("type") or ev_obj.get("relation")
                    date = ev_obj.get("date") or ev_obj.get("when") or ev_obj.get("datetime")
                    desc = ev_obj.get("description") or ev_obj.get("note")

                    parts = []
                    if planet:
                        parts.append(str(planet))
                    if aspect:
                        parts.append(str(aspect))
                    if date:
                        parts.append(str(date))

                    if parts:
                        snippet = " ".join(parts)
                        if desc:
                            snippet += f" - {desc}"
                        snippets.append(snippet)
                    else:
                        try:
                            snippets.append(json.dumps(ev_obj))
                        except Exception:
                            pass

        return snippets

    def create_sample_data(self, birth_data: Dict[str, Any]) -> List[str]:
        year = birth_data.get("year", 2007)
        month = birth_data.get("month", 7)
        date = birth_data.get("date", 23)
        return [
            f"Sun is positioned in Cancer sign in the 4th house (born {date}/{month}/{year})",
            "Moon is located in Scorpio sign in the 8th house at 15.30 degrees",
            "Mars is placed in Aries sign in the 1st house at 22.45 degrees",
            "Mercury is positioned in Gemini sign in the 3rd house at 8.20 degrees",
            "Jupiter is located in Sagittarius sign in the 9th house at 28.10 degrees",
            "Venus is placed in Taurus sign in the 2nd house at 12.55 degrees",
            "Saturn is positioned in Capricorn sign in the 10th house at 5.40 degrees",
            "Sun is in Pushya nakshatra, pada 2",
            "Moon is in Anuradha nakshatra, pada 3",
            "Mars is in Ashwini nakshatra, pada 1"
        ]

    def compute_upcoming_transits(self, birth_payload: Dict[str, Any], years: int = 2) -> List[str]:
        if swe is None:
            return []

        planet_map = {
            'sun': swe.SUN,
            'moon': swe.MOON,
            'mercury': swe.MERCURY,
            'venus': swe.VENUS,
            'mars': swe.MARS,
            'jupiter': swe.JUPITER,
            'saturn': swe.SATURN,
        }

        try:
            y = int(birth_payload.get('year'))
            m = int(birth_payload.get('month'))
            d = int(birth_payload.get('date'))
        except Exception:
            return []

        hour = float(birth_payload.get('hour') or birth_payload.get('hours') or 0)
        minute = float(birth_payload.get('minute') or birth_payload.get('minutes') or 0)
        second = float(birth_payload.get('second') or birth_payload.get('seconds') or 0)
        tz = float(birth_payload.get('timezone') or 0.0)

        local_hours = hour + minute/60.0 + second/3600.0
        ut_hours = local_hours - tz
        jd_natal = swe.julday(y, m, d, ut_hours)

        natal_long = {}
        for name in ('venus', 'jupiter'):
            p = planet_map.get(name)
            if p is None:
                continue
            try:
                lonlat = swe.calc_ut(jd_natal, p)[0]
                natal_long[name] = lonlat[0]
            except Exception:
                continue

        today = datetime.utcnow()
        today_jd = swe.julday(today.year, today.month, today.day, 0)
        end_jd = today_jd + years * 365
        found = []

        for jd in range(int(today_jd), int(end_jd)):
            for name, natal_lon in natal_long.items():
                p = planet_map.get(name)
                if p is None:
                    continue
                try:
                    tr = swe.calc_ut(jd, p)[0]
                    tr_lon = tr[0]
                    diff = abs((tr_lon - natal_lon + 180) % 360 - 180)
                    if diff <= 1.0:
                        yy, mm, dd, day_frac = swe.revjul(jd)
                        snippet = f"{name.title()} conjunct natal {name.title()} on {int(dd):02d}/{int(mm):02d}/{int(yy)} (approx)"
                        found.append(snippet)
                except Exception:
                    continue

        unique = []
        for s in found:
            if s not in unique:
                unique.append(s)
        return unique[:10]

    def fetch_all_astrology_data(self, user_id: str, birth_payload: Dict[str, Any]) -> bool:
        """Synchronous fetch and store routine. Intended to be run in background."""
        try:
            payload = birth_payload
            logger.info(f"Fetching astrology data for user {user_id} with payload keys: {list(payload.keys())}")
            api_responses: Dict[str, Any] = {}

            def post(endpoint: str):
                url = f"{self.base_url}{endpoint}"
                try:
                    resp = requests.post(url, headers=self.headers, json=payload, timeout=15)
                    return resp
                except Exception as e:
                    logger.error(f"Request to {url} failed: {e}")
                    return None

            for endpoint in ("/planets", "/planets/extended", "/transits"):
                resp = post(endpoint)
                if resp is None:
                    continue
                logger.debug(f"{endpoint} status: {resp.status_code}")
                try:
                    if resp.status_code == 200:
                        try:
                            api_responses[endpoint.strip("/").replace("/", "_")] = resp.json()
                        except Exception:
                            api_responses[endpoint.strip("/").replace("/", "_")] = {"raw": resp.text}
                    else:
                        logger.warning(f"{endpoint} returned {resp.status_code}")
                except Exception as e:
                    logger.debug(f"Error handling response from {endpoint}: {e}")

            if api_responses:
                text_snippets = self.parse_api_response(api_responses)
            else:
                text_snippets = self.create_sample_data(payload)

            if not text_snippets or len(text_snippets) < 3:
                text_snippets = self.create_sample_data(payload)

            embeddings = None

            if "transits" not in api_responses and swe is not None:
                try:
                    transit_snippets = self.compute_upcoming_transits(payload, years=2)
                    if transit_snippets:
                        text_snippets.extend(transit_snippets)
                        api_responses.setdefault("transits_local", []).extend(transit_snippets)
                except Exception:
                    logger.exception("Local transit computation failed")

            astrology_doc = {
                "user_id": user_id,
                "birth_data": payload,
                "api_responses": api_responses,
                "text_snippets": text_snippets,
                "embeddings": embeddings,
                "created_at": datetime.utcnow()
            }

            try:
                db.astrology_data.delete_many({"user_id": user_id})
                db.astrology_data.insert_one(astrology_doc)
                logger.info(f"Stored {len(text_snippets)} snippets for user {user_id}")
            except Exception as e:
                logger.exception(f"Failed to store astrology data: {e}")

            return True
        except Exception as e:
            logger.exception(f"Fetch astrology data error: {e}")
            return False
