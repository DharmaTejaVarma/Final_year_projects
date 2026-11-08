import json
import re
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException

try:
    from app.core.config import settings
    from app.core.logger import logger
    from app.schemas.ai import (
        ExtractedPreferences,
        PreferenceExtractionRequest,
        PreferenceExtractionResponse,
    )
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.logger import logger
    from backend.app.schemas.ai import (
        ExtractedPreferences,
        PreferenceExtractionRequest,
        PreferenceExtractionResponse,
    )

KNOWN_DESTINATIONS = [
    "Hyderabad",
    "Bengaluru",
    "Bangalore",
    "Delhi",
    "Mumbai",
    "Jaipur",
    "Goa",
    "Chennai",
    "Kolkata",
    "Agra",
    "Pune",
    "Mysuru",
    "Mysore",
    "Kochi",
    "Udaipur",
]

INTEREST_PATTERNS = {
    "history": [r"\bhistor(?:y|ical)\b", r"\bmonument", r"\bfort\b", r"\bpalace\b", r"\bheritage\b", r"\btomb\b"],
    "food": [r"\bfood\b", r"\bdining\b", r"\bcuisine\b", r"\bbiryani\b", r"\beat(?:ing)?\b", r"\brestaurant\b", r"\bculinary\b"],
    "photography": [r"\bphotograph(?:y|ic)?\b", r"\bphoto\b", r"\bsightseeing\b", r"\bviewpoint\b"],
    "nature": [r"\bnature\b", r"\bgarden\b", r"\bpark\b", r"\blake\b", r"\bwildlife\b", r"\bhiking\b"],
    "culture": [r"\bcultur(?:e|al)\b", r"\bmuseum\b", r"\bart\b", r"\bgallery\b", r"\btradition\b"],
    "shopping": [r"\bshopping\b", r"\bbazaar\b", r"\bmarket\b", r"\bpearls\b", r"\bcrafts?\b"],
}


class AIService:
    """Service providing natural language understanding, preference extraction, and LLM orchestration."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self._openai_client = None

    def _get_openai_client(self):
        if not self._openai_client and self.api_key and self.api_key.strip():
            try:
                import openai

                self._openai_client = openai.OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")
        return self._openai_client

    def extract_preferences_heuristic(self, text: str) -> ExtractedPreferences:
        """Deterministic NLP rule-based parser for travel preference extraction."""
        text_lower = text.lower()

        # 1. Destination Extraction
        destination: Optional[str] = None
        for dest in KNOWN_DESTINATIONS:
            if dest.lower() in text_lower:
                destination = dest
                if destination == "Bangalore":
                    destination = "Bengaluru"
                break

        if not destination:
            # Fallback regex search for pattern "trip to <Word>", "visit <Word>", "in <Word>"
            dest_match = re.search(r"(?:trip to|visit|in|explore|travel to)\s+([A-Z][a-zA-Z]+)", text)
            if dest_match:
                destination = dest_match.group(1)

        # 2. Duration Extraction
        duration_days: Optional[int] = None
        dur_match = re.search(r"(\d+)\s*(?:-| )?days?", text_lower)
        if dur_match:
            duration_days = int(dur_match.group(1))
        elif "weekend" in text_lower:
            duration_days = 2
        elif "one day" in text_lower or "a day" in text_lower:
            duration_days = 1

        # 3. Budget Extraction
        budget: Optional[float] = None
        # Check patterns like "budget is 5000", "₹5,000", "5k budget", "Rs. 10000", "budget is ?5,000"
        budget_match = re.search(r"(?:budget\s*(?:is|of)?|₹|rs\.?|inr|\$)\s*[:=]?\s*[^a-zA-Z0-9\s]?\s*(\d+(?:,\d+)*(?:\.\d+)?)", text_lower)
        if not budget_match:
            # Check pattern "5000 budget", "5000 rs"
            budget_match = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rs|rupees|inr|budget)", text_lower)
        if budget_match:
            clean_val = budget_match.group(1).replace(",", "")
            budget = float(clean_val)
        else:
            # Check for "5k", "10k"
            k_match = re.search(r"(\d+)\s*k\b", text_lower)
            if k_match:
                budget = float(k_match.group(1)) * 1000.0

        # 4. Interests Extraction
        interests: List[str] = []
        for interest_name, patterns in INTEREST_PATTERNS.items():
            for p in patterns:
                if re.search(p, text_lower):
                    interests.append(interest_name)
                    break

        if not interests:
            interests = ["history", "culture"]

        # 5. Travel Style / Pace Extraction
        travel_style = "moderate"
        if re.search(r"\b(?:relaxed|peaceful|slow|chill|easy)\b", text_lower):
            travel_style = "relaxed"
        elif re.search(r"\b(?:packed|fast|hectic|busy|active)\b", text_lower):
            travel_style = "packed"

        # 6. Transportation Mode
        transportation = "driving-car"
        if re.search(r"\b(?:walk|walking|foot)\b", text_lower):
            transportation = "foot-walking"
        elif re.search(r"\b(?:cycle|cycling|bike)\b", text_lower):
            transportation = "cycling-regular"

        # 7. Travelers Count
        travelers_count = 1
        ppl_match = re.search(r"(\d+)\s*(?:people|travelers|adults|persons?|of us)", text_lower)
        if ppl_match:
            travelers_count = max(1, int(ppl_match.group(1)))
        elif "family" in text_lower:
            travelers_count = 4
        elif "couple" in text_lower or "we " in text_lower:
            travelers_count = 2

        # 8. Clarification Check
        missing_fields: List[str] = []
        if not destination:
            missing_fields.append("destination")
        if not duration_days:
            missing_fields.append("duration_days")
        if not budget:
            missing_fields.append("budget")

        needs_clarification = len(missing_fields) > 0
        clarification_question: Optional[str] = None
        if needs_clarification:
            parts = []
            if "destination" in missing_fields:
                parts.append("which destination city you would like to visit")
            if "duration_days" in missing_fields:
                parts.append("how many days you plan to travel")
            if "budget" in missing_fields:
                parts.append("your approximate total budget")
            clarification_question = f"To customize your trip, could you let me know {' and '.join(parts)}?"

        return ExtractedPreferences(
            destination=destination,
            duration_days=duration_days,
            budget=budget,
            interests=interests,
            travel_style=travel_style,
            transportation=transportation,
            travelers_count=travelers_count,
            needs_clarification=needs_clarification,
            missing_fields=missing_fields,
            clarification_question=clarification_question,
        )

    def extract_preferences(self, text: str) -> PreferenceExtractionResponse:
        """Extract structured travel preferences using LLM when available, falling back to heuristic NLP."""
        client = self._get_openai_client()

        # If OpenAI client is available, try structured extraction
        if client is not None:
            prompt = (
                "You are a travel assistant preference parser. Extract travel parameters from the user text.\n"
                "Return pure JSON with keys: destination (string or null), duration_days (int or null), "
                "budget (float or null), interests (array of strings), travel_style ('relaxed'|'moderate'|'packed'), "
                "transportation ('driving-car'|'foot-walking'|'cycling-regular'), travelers_count (int)."
            )
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": text},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                )
                raw_json = json.loads(response.choices[0].message.content)

                dest = raw_json.get("destination")
                dur = raw_json.get("duration_days")
                budg = raw_json.get("budget")

                missing = []
                if not dest:
                    missing.append("destination")
                if not dur:
                    missing.append("duration_days")
                if not budg:
                    missing.append("budget")

                needs_clar = len(missing) > 0
                clar_q = None
                if needs_clar:
                    clar_q = f"Could you provide your {' and '.join(missing)} so I can plan your itinerary?"

                prefs = ExtractedPreferences(
                    destination=dest,
                    duration_days=dur,
                    budget=budg,
                    interests=raw_json.get("interests", ["history"]),
                    travel_style=raw_json.get("travel_style", "moderate"),
                    transportation=raw_json.get("transportation", "driving-car"),
                    travelers_count=raw_json.get("travelers_count", 1),
                    needs_clarification=needs_clar,
                    missing_fields=missing,
                    clarification_question=clar_q,
                )
                return PreferenceExtractionResponse(
                    original_text=text,
                    preferences=prefs,
                    confidence=0.95,
                    source="llm",
                )
            except Exception as e:
                logger.warning(f"OpenAI preference extraction failed: {e}. Falling back to heuristic NLP.")

        # Heuristic NLP fallback
        prefs = self.extract_preferences_heuristic(text)
        return PreferenceExtractionResponse(
            original_text=text,
            preferences=prefs,
            confidence=0.88,
            source="heuristic_nlp",
        )


ai_service = AIService()
