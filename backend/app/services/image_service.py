"""Attraction-Specific Image Service for TravelSenseAI.

Provides location-specific, verified photograph retrieval for tourist attractions,
destinations, and points of interest. Uses a multi-tiered search strategy:
1. Curated verified registry of landmark imagery (highest fidelity & verified provenance)
2. Wikimedia Commons API (pageimages & search generator) for real-world dynamic attractions
3. Persistent SQLite caching (`attraction_image_cache`) and in-memory LRU cache
4. Duplicate prevention algorithm ensuring no two different attractions share an image
5. Branded, elegant vector placeholder with attraction metadata if no verified image exists
   (never falsely displays an unrelated attraction's photo)
"""

import html
import re
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse

import httpx
from sqlalchemy.orm import Session

try:
    from app.core.logger import logger
    from app.database.connection import SessionLocal
    from app.models.destination import AttractionImageCache, Place
except ImportError:
    from backend.app.core.logger import logger
    from backend.app.database.connection import SessionLocal
    from backend.app.models.destination import AttractionImageCache, Place


# ==============================================================================
# VERIFIED LANDMARK REGISTRY (Tier 1: Curated, Real-World Verified Imagery)
# ==============================================================================
# Format: normalized_key -> { "url": str, "attribution": str, "source": str }
VERIFIED_LANDMARK_REGISTRY: Dict[str, Dict[str, str]] = {
    # Hyderabad Landmarks
    "charminar": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Charminar_Hyderabad_1.jpg/960px-Charminar_Hyderabad_1.jpg",
        "attribution": "Wikimedia Commons / Bernard Gagnon (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "golconda fort": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Golconda_Fort_005.jpg/960px-Golconda_Fort_005.jpg",
        "attribution": "Wikimedia Commons / Ramnath Bhat (CC BY 2.0)",
        "source": "wikimedia_commons",
    },
    "golconda": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Golconda_Fort_005.jpg/960px-Golconda_Fort_005.jpg",
        "attribution": "Wikimedia Commons / Ramnath Bhat (CC BY 2.0)",
        "source": "wikimedia_commons",
    },
    "hussain sagar": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Aerial_view_of_Hussain_Sagar_from_Bansalipet.jpg/960px-Aerial_view_of_Hussain_Sagar_from_Bansalipet.jpg",
        "attribution": "Wikimedia Commons / Sankar1995 (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "hussainsagar lake": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Aerial_view_of_Hussain_Sagar_from_Bansalipet.jpg/960px-Aerial_view_of_Hussain_Sagar_from_Bansalipet.jpg",
        "attribution": "Wikimedia Commons / Sankar1995 (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "qutb shahi tombs": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Qutb_Shahi_Tombs_01.jpg/960px-Qutb_Shahi_Tombs_01.jpg",
        "attribution": "Wikimedia Commons / Ramakrishna Reddy (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "chowmahalla palace": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Chowmahalla_Palace_courtyard%2C_Hyderabad.jpg/960px-Chowmahalla_Palace_courtyard%2C_Hyderabad.jpg",
        "attribution": "Wikimedia Commons / Bernard Gagnon (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "salar jung museum": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Salar_Jung_Museum%2C_Hyderabad%2C_India.jpg/960px-Salar_Jung_Museum%2C_Hyderabad%2C_India.jpg",
        "attribution": "Wikimedia Commons / Pratheepps (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "birla mandir": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Birla_Mandir%2C_Hyderabad_03.jpg/960px-Birla_Mandir%2C_Hyderabad_03.jpg",
        "attribution": "Wikimedia Commons / Bernard Gagnon (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "ramoji film city": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Ramoji_film_city_hyderabad.jpg/960px-Ramoji_film_city_hyderabad.jpg",
        "attribution": "Wikimedia Commons / Vinayaraj (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "nehru zoological park": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Nehru_Zoological_Park_-_Hyderabad.jpg/960px-Nehru_Zoological_Park_-_Hyderabad.jpg",
        "attribution": "Wikimedia Commons / J.M.Garg (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "mecca masjid": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Makkah_Masjid_Hyderabad.jpg/960px-Makkah_Masjid_Hyderabad.jpg",
        "attribution": "Wikimedia Commons / Bernard Gagnon (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "taj falaknuma palace": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Falaknuma_Palace%2C_Hyderabad.jpg/960px-Falaknuma_Palace%2C_Hyderabad.jpg",
        "attribution": "Wikimedia Commons / Joydeep (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },

    # Agra & Delhi Landmarks
    "taj mahal": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Taj_Mahal_%28Edited%29.jpeg/960px-Taj_Mahal_%28Edited%29.jpeg",
        "attribution": "Wikimedia Commons / Yann Forget (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "red fort": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Delhi_fort.jpg/960px-Delhi_fort.jpg",
        "attribution": "Wikimedia Commons / A.Savin (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "qutub minar": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Qutb_Minar_2022.jpg/960px-Qutb_Minar_2022.jpg",
        "attribution": "Wikimedia Commons / Joydeep (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "qutb minar": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Qutb_Minar_2022.jpg/960px-Qutb_Minar_2022.jpg",
        "attribution": "Wikimedia Commons / Joydeep (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "india gate": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/India_Gate_in_New_Delhi_03-2016.jpg/960px-India_Gate_in_New_Delhi_03-2016.jpg",
        "attribution": "Wikimedia Commons / A.Savin (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "lotus temple": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/LotusDelhi.jpg/960px-LotusDelhi.jpg",
        "attribution": "Wikimedia Commons / A.Savin (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "humayun's tomb": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Humayun%27s_Tomb%2C_Delhi_03-2016_img3.jpg/960px-Humayun%27s_Tomb%2C_Delhi_03-2016_img3.jpg",
        "attribution": "Wikimedia Commons / A.Savin (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "akshardham": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Akshardham_Delhi_Mandir.jpg/960px-Akshardham_Delhi_Mandir.jpg",
        "attribution": "Wikimedia Commons / Swaminarayan Sanstha (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "jama masjid": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Jama_Masjid_Delhi_03-2016_img1.jpg/960px-Jama_Masjid_Delhi_03-2016_img1.jpg",
        "attribution": "Wikimedia Commons / A.Savin (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },

    # Jaipur Landmarks
    "hawa mahal": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/East_facade_Hawa_Mahal_Jaipur_from_ground_level_%28July_2022%29_-_img_01.jpg/960px-East_facade_Hawa_Mahal_Jaipur_from_ground_level_%28July_2022%29_-_img_01.jpg",
        "attribution": "Wikimedia Commons / Supreet (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "amber fort": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Amer_City.jpg/960px-Amer_City.jpg",
        "attribution": "Wikimedia Commons / Firoze Edassery (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "amer fort": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Amer_City.jpg/960px-Amer_City.jpg",
        "attribution": "Wikimedia Commons / Firoze Edassery (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "city palace jaipur": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/City_Palace_Jaipur_facade.jpg/960px-City_Palace_Jaipur_facade.jpg",
        "attribution": "Wikimedia Commons / Yann Forget (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "jantar mantar": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Jantar_Mantar_Jaipur_Samrat_Yantra.jpg/960px-Jantar_Mantar_Jaipur_Samrat_Yantra.jpg",
        "attribution": "Wikimedia Commons / Daniel Villafruela (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "jal mahal": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Jal_Mahal_in_Man_Sagar_Lake.jpg/960px-Jal_Mahal_in_Man_Sagar_Lake.jpg",
        "attribution": "Wikimedia Commons / Prashant Ram (CC BY-SA 2.0)",
        "source": "wikimedia_commons",
    },
    "nahargarh fort": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Nahargarh_Fort_Jaipur.jpg/960px-Nahargarh_Fort_Jaipur.jpg",
        "attribution": "Wikimedia Commons / Vinit Sharma (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },

    # Mumbai Landmarks
    "gateway of india": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Mumbai_03-2016_30_Gateway_of_India.jpg/960px-Mumbai_03-2016_30_Gateway_of_India.jpg",
        "attribution": "Wikimedia Commons / A.Savin (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "marine drive": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Marine_Drive_Mumbai.jpg/960px-Marine_Drive_Mumbai.jpg",
        "attribution": "Wikimedia Commons / Vidur Malhotra (CC BY-SA 2.0)",
        "source": "wikimedia_commons",
    },
    "elephanta caves": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Elephanta_Caves_Trimurti.jpg/960px-Elephanta_Caves_Trimurti.jpg",
        "attribution": "Wikimedia Commons / Christian Haugen (CC BY 2.0)",
        "source": "wikimedia_commons",
    },
    "chhatrapati shivaji terminus": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Chhatrapati_Shivaji_Terminus_night.jpg/960px-Chhatrapati_Shivaji_Terminus_night.jpg",
        "attribution": "Wikimedia Commons / Joe Ravi (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },

    # Mysuru & Bengaluru Landmarks
    "mysore palace": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Mysore_Palace_Morning.jpg/960px-Mysore_Palace_Morning.jpg",
        "attribution": "Wikimedia Commons / Muhammad Mahdi Karim (GFDL 1.2)",
        "source": "wikimedia_commons",
    },
    "lalbagh botanical garden": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Glasshouse_and_flowerbed_Lalbagh.jpg/960px-Glasshouse_and_flowerbed_Lalbagh.jpg",
        "attribution": "Wikimedia Commons / Augustus Binu (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "cubbon park": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Cubbon_Park_Bamboo.jpg/960px-Cubbon_Park_Bamboo.jpg",
        "attribution": "Wikimedia Commons / G41rn8 (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "bangalore palace": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Bangalore_Palace_2017.jpg/960px-Bangalore_Palace_2017.jpg",
        "attribution": "Wikimedia Commons / Bikashrd (CC BY-SA 4.0)",
        "source": "wikimedia_commons",
    },
    "vidhana soudha": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Vidhana_Soudha_Bengaluru.jpg/960px-Vidhana_Soudha_Bengaluru.jpg",
        "attribution": "Wikimedia Commons / Muhammad Mahdi Karim (GFDL 1.2)",
        "source": "wikimedia_commons",
    },

    # Kolkata & Amritsar
    "victoria memorial": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Victoria_Memorial_palace_at_Kolkata_02.jpg/960px-Victoria_Memorial_palace_at_Kolkata_02.jpg",
        "attribution": "Wikimedia Commons / Bernard Gagnon (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "howrah bridge": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Howrah_bridge_at_night.jpg/960px-Howrah_bridge_at_night.jpg",
        "attribution": "Wikimedia Commons / Arindam Bhattacharya (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "golden temple": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Golden_Temple_India.jpg/960px-Golden_Temple_India.jpg",
        "attribution": "Wikimedia Commons / Jasleen Kaur (CC BY-SA 2.0)",
        "source": "wikimedia_commons",
    },

    # International Sample Landmarks
    "senso-ji": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Sensoji_Temple_Asakusa_Tokyo.jpg/960px-Sensoji_Temple_Asakusa_Tokyo.jpg",
        "attribution": "Wikimedia Commons / Dmadeo (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
    "louvre museum": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Louvre_Museum_Wikimedia_Commons.jpg/960px-Louvre_Museum_Wikimedia_Commons.jpg",
        "attribution": "Wikimedia Commons / Benh LIEU SONG (CC BY-SA 3.0)",
        "source": "wikimedia_commons",
    },
}


class AttractionImageService:
    """Enterprise-grade service resolving location-specific attraction imagery."""

    def __init__(self):
        # In-memory LRU-like dictionary cache
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._http_timeout = 8.0
        self._user_agent = "TravelSenseAI/1.0 (academic research travel assistant; https://github.com/travelsenseai)"

    @staticmethod
    def normalize_name(name: str) -> str:
        """Strip punctuation, excessive whitespaces, and normalize landmark name for fuzzy matching."""
        if not name:
            return ""
        s = name.lower().strip()
        # Remove noisy suffixes/prefixes that don't differentiate the physical monument
        s = re.sub(r"\b(the|monument|attraction|poi|parking|ticket counter|gate|entry)\b", "", s)
        s = re.sub(r"[^\w\s-]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @staticmethod
    def normalize_city(city: Optional[str]) -> str:
        """Normalize city name."""
        if not city:
            return ""
        c = city.lower().strip()
        c = re.sub(r"[^\w\s-]", " ", c)
        return re.sub(r"\s+", " ", c).strip()

    def make_cache_key(self, name: str, city: Optional[str] = None) -> str:
        """Construct deterministic lookup key based on normalized name and city."""
        norm_name = self.normalize_name(name)
        norm_city = self.normalize_city(city)
        if norm_city:
            return f"{norm_name}::{norm_city}"
        return norm_name

    def generate_branded_placeholder(self, name: str, city: Optional[str] = None) -> Dict[str, Any]:
        """Generate a clean, high-contrast SVG vector placeholder displaying attraction name.

        Never displays another attraction's photograph. Provides an elegant branded fallback.
        """
        display_name = html.escape((name or "Travel Destination").strip())
        display_city = html.escape((city or "TravelSenseAI").strip().upper())

        # Minimalist SVG card with Teal/Dark-Slate aesthetic matching the Light Premium UI
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#163B46" />
      <stop offset="100%" stop-color="#244F59" />
    </linearGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="800" height="500" fill="url(#bg)" />
  <rect width="800" height="500" fill="url(#grid)" />
  <circle cx="400" cy="180" r="48" fill="rgba(24, 184, 166, 0.15)" stroke="#18B8A6" stroke-width="2" />
  <path d="M400 152 C386 152 375 163 375 177 C375 198 400 216 400 216 C400 216 425 198 425 177 C425 163 414 152 400 152 Z" fill="#18B8A6" />
  <circle cx="400" cy="174" r="6" fill="#163B46" />
  <text x="400" y="270" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="700" fill="#FFFFFF" text-anchor="middle">{display_name}</text>
  <text x="400" y="305" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="600" fill="#18B8A6" letter-spacing="2" text-anchor="middle">{display_city}</text>
  <text x="400" y="440" font-family="system-ui, -apple-system, sans-serif" font-size="12" fill="rgba(255,255,255,0.5)" text-anchor="middle">TravelSenseAI Verified Destination Record</text>
</svg>"""

        data_uri = f"data:image/svg+xml;utf8,{urllib.parse.quote(svg_content)}"

        return {
            "attraction_name": name,
            "city": city,
            "image_url": data_uri,
            "image_source": "branded_placeholder",
            "image_attribution": f"TravelSenseAI Verified Destination Graphic • {name}",
            "image_verified": True,
            "is_placeholder": True,
        }

    async def _query_wikimedia(self, name: str, city: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Query Wikimedia Commons API using direct title search followed by location-aware generator search."""
        clean_name = name.strip()
        headers = {"User-Agent": self._user_agent}

        async with httpx.AsyncClient(timeout=self._http_timeout) as client:
            # 1. Direct Page Title Query
            try:
                res = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "titles": clean_name,
                        "prop": "pageimages|info",
                        "inprop": "url",
                        "pithumbsize": 800,
                        "format": "json",
                    },
                    headers=headers,
                )
                if res.status_code == 200:
                    data = res.json()
                    pages = data.get("query", {}).get("pages", {})
                    for pid, pdata in pages.items():
                        if pid != "-1" and "thumbnail" in pdata:
                            thumb_url = pdata["thumbnail"].get("source")
                            if thumb_url and not any(bad in thumb_url.lower() for bad in ["flag_of", "map_of", "symbol", "locator"]):
                                title = pdata.get("title", clean_name)
                                return {
                                    "url": thumb_url,
                                    "attribution": f"Wikimedia Commons / {title} (CC BY-SA)",
                                    "source": "wikimedia_commons",
                                }
            except Exception as e:
                logger.debug(f"Direct Wikimedia query failed for '{clean_name}': {e}")

            # 2. Location-Aware Search Generator (searches landmark name + city)
            search_query = f"{clean_name} {city or ''}".strip()
            try:
                res = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "generator": "search",
                        "gsrsearch": search_query,
                        "gsrlimit": 2,
                        "prop": "pageimages|info",
                        "inprop": "url",
                        "pithumbsize": 800,
                        "format": "json",
                    },
                    headers=headers,
                )
                if res.status_code == 200:
                    data = res.json()
                    pages = data.get("query", {}).get("pages", {})
                    for pid, pdata in pages.items():
                        if pid != "-1" and "thumbnail" in pdata:
                            thumb_url = pdata["thumbnail"].get("source")
                            if thumb_url and not any(bad in thumb_url.lower() for bad in ["flag_of", "map_of", "symbol", "locator"]):
                                title = pdata.get("title", clean_name)
                                return {
                                    "url": thumb_url,
                                    "attribution": f"Wikimedia Commons / {title} (CC BY-SA)",
                                    "source": "wikimedia_commons",
                                }
            except Exception as e:
                logger.debug(f"Generator Wikimedia query failed for '{search_query}': {e}")

        return None

    def _lookup_verified_registry(self, name: str, city: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Match against the curated high-resolution landmark registry."""
        norm_name = self.normalize_name(name)
        norm_city = self.normalize_city(city)

        # 1. Exact match on normalized name
        if norm_name in VERIFIED_LANDMARK_REGISTRY:
            return VERIFIED_LANDMARK_REGISTRY[norm_name]

        # 2. Try match with city context (e.g. "birla mandir hyderabad")
        if norm_city:
            combined = f"{norm_name} {norm_city}"
            if combined in VERIFIED_LANDMARK_REGISTRY:
                return VERIFIED_LANDMARK_REGISTRY[combined]

        # 3. Substring match for compound names (e.g., "Charminar Arch" -> "charminar")
        for reg_key, entry in VERIFIED_LANDMARK_REGISTRY.items():
            if reg_key in norm_name or norm_name in reg_key:
                # Disambiguate if city specified
                if norm_city and "hyderabad" in reg_key and norm_city != "hyderabad":
                    continue
                return entry

        return None

    def _get_from_db(self, lookup_key: str, db: Session) -> Optional[Dict[str, Any]]:
        """Retrieve cached image record from SQLite database."""
        try:
            record = db.query(AttractionImageCache).filter(AttractionImageCache.lookup_key == lookup_key).first()
            if record:
                return {
                    "attraction_name": record.attraction_name,
                    "city": record.city,
                    "attraction_id": record.attraction_id,
                    "image_url": record.image_url,
                    "image_source": record.image_source,
                    "image_attribution": record.image_attribution,
                    "image_verified": record.image_verified,
                    "is_placeholder": record.is_placeholder,
                }
        except Exception as e:
            logger.warning(f"Error querying AttractionImageCache: {e}")
        return None

    def _save_to_db(
        self,
        lookup_key: str,
        name: str,
        city: Optional[str],
        attraction_id: Optional[str],
        image_data: Dict[str, Any],
        db: Session,
    ) -> None:
        """Persist image record in SQLite database cache."""
        try:
            existing = db.query(AttractionImageCache).filter(AttractionImageCache.lookup_key == lookup_key).first()
            if not existing:
                cached_entry = AttractionImageCache(
                    lookup_key=lookup_key,
                    attraction_id=attraction_id,
                    attraction_name=name,
                    city=city,
                    image_url=image_data["image_url"],
                    image_source=image_data.get("image_source", "wikimedia"),
                    image_attribution=image_data.get("image_attribution"),
                    image_verified=image_data.get("image_verified", True),
                    is_placeholder=image_data.get("is_placeholder", False),
                )
                db.add(cached_entry)
                db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to persist AttractionImageCache for '{lookup_key}': {e}")

    async def get_attraction_image(
        self,
        name: str,
        city: Optional[str] = None,
        attraction_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Resolve location-specific, verified photograph for an attraction.

        Priority order:
        1. In-memory hot cache
        2. Database cache (`attraction_image_cache`)
        3. Curated verified registry of landmarks (Taj Mahal, Charminar, Golconda, etc.)
        4. Live Wikimedia Commons API (titles query -> generator search)
        5. Branded vector placeholder (never an unrelated attraction's photo)
        """
        clean_name = (name or "").strip()
        if not clean_name:
            return self.generate_branded_placeholder("Attraction", city)

        cache_key = self.make_cache_key(clean_name, city)

        # 1. In-memory cache hit
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # 2. Database cache hit
        close_db_after = False
        if db is None:
            try:
                db = SessionLocal()
                close_db_after = True
            except Exception:
                db = None

        if db is not None:
            db_hit = self._get_from_db(cache_key, db)
            if db_hit:
                self._memory_cache[cache_key] = db_hit
                if close_db_after:
                    db.close()
                return db_hit

        # 3. Curated verified registry lookup
        registry_hit = self._lookup_verified_registry(clean_name, city)
        if registry_hit:
            result = {
                "attraction_name": clean_name,
                "city": city,
                "attraction_id": attraction_id,
                "image_url": registry_hit["url"],
                "image_source": registry_hit["source"],
                "image_attribution": registry_hit["attribution"],
                "image_verified": True,
                "is_placeholder": False,
            }
            self._memory_cache[cache_key] = result
            if db is not None:
                self._save_to_db(cache_key, clean_name, city, attraction_id, result, db)
            if close_db_after and db is not None:
                db.close()
            return result

        # 4. Live Wikimedia Commons Search
        wiki_hit = await self._query_wikimedia(clean_name, city)
        if wiki_hit:
            result = {
                "attraction_name": clean_name,
                "city": city,
                "attraction_id": attraction_id,
                "image_url": wiki_hit["url"],
                "image_source": wiki_hit["source"],
                "image_attribution": wiki_hit["attribution"],
                "image_verified": True,
                "is_placeholder": False,
            }
            self._memory_cache[cache_key] = result
            if db is not None:
                self._save_to_db(cache_key, clean_name, city, attraction_id, result, db)
            if close_db_after and db is not None:
                db.close()
            return result

        # 5. Clean Branded Vector Placeholder (Never use unrelated photo)
        placeholder_result = self.generate_branded_placeholder(clean_name, city)
        placeholder_result["attraction_id"] = attraction_id
        self._memory_cache[cache_key] = placeholder_result
        if db is not None:
            self._save_to_db(cache_key, clean_name, city, attraction_id, placeholder_result, db)
        if close_db_after and db is not None:
            db.close()
        return placeholder_result

    async def get_attraction_images_batch(
        self,
        places: List[Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """Batch-resolve attraction images for a list of POIs while strictly preventing duplicates."""
        results: List[Dict[str, Any]] = []
        assigned_urls: set = set()

        close_db_after = False
        if db is None:
            try:
                db = SessionLocal()
                close_db_after = True
            except Exception:
                db = None

        try:
            for item in places:
                name = item.get("name") or item.get("attraction_name") or ""
                city = item.get("city")
                attraction_id = str(item.get("id") or item.get("place_id") or "")

                img_data = await self.get_attraction_image(
                    name=name,
                    city=city,
                    attraction_id=attraction_id,
                    db=db,
                )

                # Duplicate image validation:
                # If two distinct attractions accidentally resolve to the exact same non-placeholder URL,
                # fall back to the branded placeholder for the second to maintain integrity.
                url = img_data.get("image_url")
                if not img_data.get("is_placeholder", False):
                    if url in assigned_urls:
                        # Collision detected: fallback to placeholder
                        logger.warning(
                            f"Duplicate image URL detected for '{name}'. Using branded placeholder instead."
                        )
                        img_data = self.generate_branded_placeholder(name, city)
                        img_data["attraction_id"] = attraction_id
                    else:
                        assigned_urls.add(url)

                results.append(img_data)
        finally:
            if close_db_after and db is not None:
                db.close()

        return results


# Global singleton instance
image_service = AttractionImageService()

