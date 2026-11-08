from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ExtractedPreferences(BaseModel):
    """Structured travel preferences extracted from natural-language user requests."""

    destination: Optional[str] = Field(default=None, description="Target destination city or region")
    duration_days: Optional[int] = Field(default=None, ge=1, le=30, description="Trip duration in calendar days")
    budget: Optional[float] = Field(default=None, ge=0.0, description="Estimated total budget in currency units (e.g. INR)")
    interests: List[str] = Field(default_factory=list, description="Specific themes, attractions, or activity interests")
    travel_style: Optional[str] = Field(
        default="moderate",
        description="Pacing style: 'relaxed' (fewer stops), 'moderate', or 'packed' (fast-paced)",
    )
    transportation: Optional[str] = Field(
        default="driving-car",
        description="Mode of travel: 'driving-car', 'foot-walking', or 'cycling-regular'",
    )
    travelers_count: int = Field(default=1, ge=1, le=50, description="Number of travelers")
    needs_clarification: bool = Field(default=False, description="True if essential criteria are missing")
    missing_fields: List[str] = Field(default_factory=list, description="List of essential fields that need clarification")
    clarification_question: Optional[str] = Field(
        default=None, description="Targeted natural-language question asking for missing parameters"
    )


class PreferenceExtractionRequest(BaseModel):
    """Request payload to extract structured preferences from natural language."""

    text: str = Field(..., min_length=2, max_length=1500, description="User's natural language travel inquiry")


class PreferenceExtractionResponse(BaseModel):
    """Response containing extracted structured travel preferences."""

    original_text: str
    preferences: ExtractedPreferences
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    source: str = Field(default="llm", description="'llm' or 'heuristic_nlp'")


class ChatMessage(BaseModel):
    """Message in conversation history."""

    role: str = Field(..., pattern="^(user|assistant|system)$", description="'user', 'assistant', or 'system'")
    content: str = Field(..., min_length=1, max_length=5000)


class SourceDocument(BaseModel):
    """Curated knowledge document chunk retrieved via RAG."""

    title: str
    source: str
    category: str
    destination: str
    content: str
    relevance_score: Optional[float] = None


class AIChatRequest(BaseModel):
    """Request payload for multi-turn AI travel assistant conversation."""

    message: str = Field(..., min_length=1, max_length=2000, description="User input message or question")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None, description="Prior conversation context"
    )
    session_id: Optional[str] = Field(default=None, description="Client or user session identifier")
    destination_hint: Optional[str] = Field(default=None, description="Optional destination hint if already known")


class AIChatResponse(BaseModel):
    """Response payload from AI travel assistant backed by LangGraph and RAG."""

    reply: str
    intent: str
    extracted_preferences: Optional[ExtractedPreferences] = None
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    retrieved_sources: List[SourceDocument] = Field(default_factory=list)
    recommendations: Optional[List[Dict[str, Any]]] = None
    itinerary: Optional[Dict[str, Any]] = None
    weather_context: Optional[Dict[str, Any]] = None
    workflow_trace: List[str] = Field(default_factory=list)
