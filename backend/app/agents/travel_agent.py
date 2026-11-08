from typing import Any, Dict, List, Optional

try:
    from app.agents.state import AgentState
    from app.agents.workflow import travel_graph
    from app.core.logger import logger
    from app.schemas.ai import (
        AIChatRequest,
        AIChatResponse,
        ExtractedPreferences,
        SourceDocument,
    )
except ImportError:
    from backend.app.agents.state import AgentState
    from backend.app.agents.workflow import travel_graph
    from backend.app.core.logger import logger
    from backend.app.schemas.ai import (
        AIChatRequest,
        AIChatResponse,
        ExtractedPreferences,
        SourceDocument,
    )


class TravelAgent:
    """Conversational travel assistant executing the LangGraph multi-node workflow."""

    def __init__(self, graph=travel_graph):
        self.graph = graph

    async def chat(self, request: AIChatRequest) -> AIChatResponse:
        """Process user message through LangGraph and return structured response."""
        logger.info(f"TravelAgent processing user message: '{request.message[:80]}...'")

        # Convert conversation history
        history: List[Dict[str, str]] = []
        if request.conversation_history:
            history = [{"role": m.role, "content": m.content} for m in request.conversation_history]

        initial_state: AgentState = {
            "user_query": request.message,
            "messages": history,
            "session_id": request.session_id,
            "destination": request.destination_hint,
            "workflow_trace": [],
        }

        # Run through LangGraph
        result_state: AgentState = await self.graph.ainvoke(initial_state)

        # Parse extracted preferences if present
        prefs_obj: Optional[ExtractedPreferences] = None
        if result_state.get("preferences"):
            try:
                prefs_obj = ExtractedPreferences(**result_state["preferences"])
            except Exception:
                prefs_obj = None

        # Parse RAG source documents
        source_docs: List[SourceDocument] = []
        for s in result_state.get("rag_sources", []):
            try:
                source_docs.append(SourceDocument(**s))
            except Exception:
                pass

        return AIChatResponse(
            reply=result_state.get("final_response", "I could not formulate a response."),
            intent=result_state.get("intent", "general_qa"),
            extracted_preferences=prefs_obj,
            needs_clarification=result_state.get("needs_clarification", False),
            clarification_question=result_state.get("clarification_question"),
            retrieved_sources=source_docs,
            recommendations=result_state.get("recommendations"),
            itinerary=result_state.get("itinerary"),
            weather_context=result_state.get("weather_info"),
            workflow_trace=result_state.get("workflow_trace", []),
        )


travel_agent = TravelAgent()

