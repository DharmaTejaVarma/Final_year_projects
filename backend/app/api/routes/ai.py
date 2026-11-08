from fastapi import APIRouter, status

try:
    from app.agents.travel_agent import travel_agent
    from app.schemas.ai import (
        AIChatRequest,
        AIChatResponse,
        PreferenceExtractionRequest,
        PreferenceExtractionResponse,
    )
    from app.services.ai_service import ai_service
except ImportError:
    from backend.app.agents.travel_agent import travel_agent
    from backend.app.schemas.ai import (
        AIChatRequest,
        AIChatResponse,
        PreferenceExtractionRequest,
        PreferenceExtractionResponse,
    )
    from backend.app.services.ai_service import ai_service

router = APIRouter(prefix="/ai", tags=["AI Travel Assistant & RAG"])


@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-turn conversational travel assistant (LangGraph + RAG)",
    description=(
        "Executes a stateful LangGraph 8-node pipeline orchestrating natural language understanding, "
        "preference extraction, ChromaDB RAG retrieval, real-time weather forecasting, context-aware "
        "POI recommendation, 2-Opt route optimization, constraint validation, and source-grounded explanations. "
        "Deterministic travel facts (distances, durations, weather, hours, ticket fees) are never hallucinated."
    ),
)
async def chat_with_assistant(payload: AIChatRequest) -> AIChatResponse:
    """Conversational endpoint executing LangGraph travel agent."""
    return await travel_agent.chat(payload)


@router.post(
    "/extract-preferences",
    response_model=PreferenceExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured travel preferences from natural language",
    description=(
        "Extracts structured travel parameters (destination, duration_days, budget, interests, "
        "travel_style, transportation, travelers_count) using LLM structured output or deterministic "
        "NLP heuristic fallback. Identifies missing essential criteria and generates targeted clarification questions."
    ),
)
async def extract_travel_preferences(payload: PreferenceExtractionRequest) -> PreferenceExtractionResponse:
    """Natural language preference extraction endpoint."""
    return ai_service.extract_preferences(payload.text)

