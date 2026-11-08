from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Shared state container transitioning across LangGraph nodes."""

    # Conversation and input
    user_query: str
    messages: List[Dict[str, str]]
    session_id: Optional[str]

    # Intent and NLU
    intent: str  # 'plan_trip', 'general_qa', 'clarify', 'explain_recommendation', 'budget_advice', 'weather_query'
    destination: Optional[str]
    preferences: Optional[Dict[str, Any]]
    needs_clarification: bool
    clarification_question: Optional[str]

    # Deterministic Service Outputs
    rag_sources: List[Dict[str, Any]]
    weather_info: Optional[Dict[str, Any]]
    recommendations: Optional[List[Dict[str, Any]]]
    itinerary: Optional[Dict[str, Any]]
    validation_report: Optional[Dict[str, Any]]

    # Output and Trace
    final_response: str
    workflow_trace: List[str]

