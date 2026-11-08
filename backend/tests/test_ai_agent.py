import asyncio
import pytest
from fastapi.testclient import TestClient

try:
    from app.agents.travel_agent import travel_agent
    from app.agents.workflow import understand_request_node
    from app.main import app
    from app.rag.document_loader import KnowledgeDocument, load_curated_documents
    from app.rag.retriever import retriever
    from app.rag.text_splitter import RecursiveCharacterTextSplitter
    from app.schemas.ai import AIChatRequest, SourceDocument
    from app.services.ai_service import ai_service
except ImportError:
    from backend.app.agents.travel_agent import travel_agent
    from backend.app.agents.workflow import understand_request_node
    from backend.app.main import app
    from backend.app.rag.document_loader import KnowledgeDocument, load_curated_documents
    from backend.app.rag.retriever import retriever
    from backend.app.rag.text_splitter import RecursiveCharacterTextSplitter
    from backend.app.schemas.ai import AIChatRequest, SourceDocument
    from backend.app.services.ai_service import ai_service

client = TestClient(app)


# ==============================================================================
# 1. NATURAL LANGUAGE UNDERSTANDING & PREFERENCE EXTRACTION
# ==============================================================================

def test_preference_extraction_full_query():
    """Verify end-to-end extraction from the exact user prompt specification:
    'I want a relaxed 2-day trip to Hyderabad. I like historical places and good food. My budget is ₹5,000.'
    """
    text = "I want a relaxed 2-day trip to Hyderabad. I like historical places and good food. My budget is ₹5,000."
    res = ai_service.extract_preferences(text)

    assert res.preferences.destination == "Hyderabad"
    assert res.preferences.duration_days == 2
    assert res.preferences.budget == 5000.0
    assert "history" in res.preferences.interests
    assert "food" in res.preferences.interests
    assert res.preferences.travel_style == "relaxed"
    assert res.preferences.needs_clarification is False
    assert len(res.preferences.missing_fields) == 0


def test_preference_extraction_clarification_missing_fields():
    """Verify system detects missing essential fields and generates targeted clarification questions."""
    text = "Plan an exciting vacation for me."
    res = ai_service.extract_preferences(text)

    assert res.preferences.needs_clarification is True
    assert "destination" in res.preferences.missing_fields
    assert "duration_days" in res.preferences.missing_fields
    assert "budget" in res.preferences.missing_fields
    assert res.preferences.clarification_question is not None
    assert "destination" in res.preferences.clarification_question.lower()


def test_preference_extraction_partial_info():
    """Verify partial extraction correctly identifies which specific field is still missing."""
    text = "Trip to Goa with a budget of ₹15,000"
    res = ai_service.extract_preferences(text)

    assert res.preferences.destination == "Goa"
    assert res.preferences.budget == 15000.0
    assert res.preferences.duration_days is None
    assert res.preferences.needs_clarification is True
    assert "duration_days" in res.preferences.missing_fields


def test_preference_extraction_styles_and_transport():
    """Verify extraction of walking transport, packed pace, and traveler count."""
    text = "A fast packed 3 days walking tour in Bengaluru with Rs 4000 for 2 people"
    res = ai_service.extract_preferences(text)

    assert res.preferences.destination == "Bengaluru"
    assert res.preferences.duration_days == 3
    assert res.preferences.budget == 4000.0
    assert res.preferences.travel_style == "packed"
    assert res.preferences.transportation == "foot-walking"
    assert res.preferences.travelers_count == 2
    assert res.preferences.needs_clarification is False


def test_preference_extraction_k_notation_budget():
    """Verify budget parsing with '5k' notation."""
    text = "Weekend trip to Hyderabad with 8k budget for history and culture"
    res = ai_service.extract_preferences(text)

    assert res.preferences.destination == "Hyderabad"
    assert res.preferences.duration_days == 2
    assert res.preferences.budget == 8000.0
    assert "history" in res.preferences.interests


# ==============================================================================
# 2. RAG IMPLEMENTATION & GROUNDING TESTS
# ==============================================================================

def test_recursive_text_splitter():
    """Verify text splitter chunks content while maintaining overlap and boundary integrity."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
    sample_text = (
        "Golconda Fort was built by the Kakatiya dynasty in the 13th century. "
        "It later became the fortified capital of the Qutb Shahi dynasty. "
        "The acoustic system is legendary: a clap at the Fateh Darwaza can be heard clearly at the Bala Hissar pavilion."
    )
    chunks = splitter.split_text(sample_text)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 150  # Boundary buffer


def test_rag_document_loader_curated_knowledge():
    """Verify curated knowledge base loads comprehensive records with proper metadata."""
    docs = load_curated_documents()

    assert len(docs) >= 8
    destinations = {d.destination for d in docs}
    assert "Hyderabad" in destinations
    assert "Bengaluru" in destinations

    categories = {d.category for d in docs}
    assert "history" in categories
    assert "culture" in categories
    assert "travel_tips" in categories

    for doc in docs:
        assert doc.title
        assert doc.source
        assert len(doc.content) > 30


def test_rag_retrieval_semantic_search():
    """Verify retriever retrieves relevant knowledge chunks for destination inquiries."""
    results = retriever.retrieve(
        query="Tell me about the acoustic clapping system at Golconda Fort",
        destination="Hyderabad",
        top_k=2,
    )

    assert len(results) >= 1
    top_doc = results[0]
    assert "Golconda" in top_doc.title or "Golconda" in top_doc.content
    assert top_doc.destination == "Hyderabad"
    assert top_doc.source


def test_rag_retrieval_cuisine_knowledge():
    """Verify retriever surfaces food culture facts for culinary inquiries."""
    results = retriever.retrieve(
        query="What is the authentic recipe and history of Hyderabadi Biryani and Irani chai?",
        destination="Hyderabad",
        top_k=2,
    )

    assert len(results) >= 1
    found_food = any("Biryani" in r.content or "Chai" in r.content or r.category in ["cuisine", "culture"] for r in results)
    assert found_food is True


def test_rag_source_grounding_and_attribution():
    """Verify synthesized answer clearly attributes sources and distinguishes verified facts."""
    test_sources = [
        SourceDocument(
            title="Charminar & Laad Bazaar",
            source="Telangana Tourism Official Archives",
            category="heritage",
            destination="Hyderabad",
            content="Built in 1591 CE by Muhammad Quli Qutb Shah. Famous for lac bangles.",
            relevance_score=0.92,
        )
    ]
    answer = retriever.generate_grounded_answer(
        query="Tell me about Charminar",
        sources=test_sources,
    )

    assert "Verified Knowledge Base Facts:" in answer
    assert "Telangana Tourism Official Archives" in answer
    assert "Charminar & Laad Bazaar" in answer
    assert "Source Grounding" in answer


def test_rag_empty_retrieval_safe_fallback():
    """Verify retriever does not hallucinate when knowledge base has no matches."""
    empty_answer = retriever.generate_grounded_answer(
        query="Unknown alien civilization",
        sources=[],
    )

    assert "could not find verified" in empty_answer.lower()
    assert "historical or cultural records" in empty_answer.lower()


# ==============================================================================
# 3. LANGGRAPH WORKFLOW & MULTI-NODE COORDINATION
# ==============================================================================

def test_workflow_understand_request_intents():
    """Verify request understanding node correctly classifies distinct user intents."""
    # Intent: plan_trip
    res1 = asyncio.run(understand_request_node({"user_query": "Plan a 2-day itinerary for Hyderabad"}))
    assert res1["intent"] == "plan_trip"
    assert res1["destination"] == "Hyderabad"

    # Intent: explain_recommendation
    res2 = asyncio.run(understand_request_node({"user_query": "Why did you recommend Chowmahalla Palace?"}))
    assert res2["intent"] == "explain_recommendation"

    # Intent: budget_advice
    res3 = asyncio.run(understand_request_node({"user_query": "How can I reduce the budget and travel cost?"}))
    assert res3["intent"] == "budget_advice"

    # Intent: weather_query
    res4 = asyncio.run(understand_request_node({"user_query": "What is the weather forecast and is it raining in Hyderabad?"}))
    assert res4["intent"] == "weather_query"

    # Intent: general_qa
    res5 = asyncio.run(understand_request_node({"user_query": "Tell me about local culture and history"}))
    assert res5["intent"] == "general_qa"


def test_langgraph_general_qa_execution():
    """Verify LangGraph executes general QA workflow with RAG retrieval and trace logging."""
    req = AIChatRequest(
        message="What is the significance of the Qutb Shahi Tombs?",
        destination_hint="Hyderabad",
    )
    res = asyncio.run(travel_agent.chat(req))

    assert res.reply is not None
    assert len(res.reply) > 50
    assert len(res.retrieved_sources) >= 1
    assert "Node 1: understand_request_node" in res.workflow_trace
    assert "Node 3: retrieve_tourism_data_node" in res.workflow_trace
    assert "Node 8: generate_explanation_node" in res.workflow_trace


def test_langgraph_clarification_branch():
    """Verify LangGraph branches directly to explanation when essential travel details are missing."""
    req = AIChatRequest(
        message="I need a vacation plan.",
    )
    res = asyncio.run(travel_agent.chat(req))

    assert res.needs_clarification is True
    assert res.clarification_question is not None
    assert "clarify" in res.reply.lower() or "let me know" in res.reply.lower()


def test_langgraph_full_trip_planning_workflow():
    """Verify LangGraph executes the entire 8-node pipeline for full itinerary planning."""
    req = AIChatRequest(
        message="Plan a relaxed 2-day trip to Hyderabad with budget ₹5000",
        destination_hint="Hyderabad",
    )
    res = asyncio.run(travel_agent.chat(req))

    assert res.intent == "plan_trip"
    assert res.needs_clarification is False
    assert res.extracted_preferences is not None
    assert res.extracted_preferences.destination == "Hyderabad"
    assert res.extracted_preferences.duration_days == 2

    # Check 8-node pipeline execution trace
    assert "Node 1: understand_request_node" in res.workflow_trace
    assert "Node 2: extract_preferences_node" in res.workflow_trace
    assert "Node 4: fetch_weather_context_node" in res.workflow_trace
    assert "Node 5: generate_recommendations_node" in res.workflow_trace
    assert "Node 6: plan_routes_and_itinerary_node" in res.workflow_trace
    assert "Node 7: validate_itinerary_node" in res.workflow_trace
    assert "Node 8: generate_explanation_node" in res.workflow_trace

    # Check itinerary and recommendations artifacts
    assert res.recommendations is not None
    assert len(res.recommendations) > 0
    assert res.itinerary is not None
    assert res.itinerary.get("total_days") == 2
    assert "Planned 2-Day Itinerary for Hyderabad" in res.reply


# ==============================================================================
# 4. REST API ENDPOINTS
# ==============================================================================

def test_api_extract_preferences_endpoint():
    """Verify POST /api/ai/extract-preferences endpoint."""
    response = client.post(
        "/api/ai/extract-preferences",
        json={"text": "I want a 2-day historical trip to Hyderabad with budget 5000"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["original_text"] == "I want a 2-day historical trip to Hyderabad with budget 5000"
    assert data["preferences"]["destination"] == "Hyderabad"
    assert data["preferences"]["duration_days"] == 2
    assert data["preferences"]["budget"] == 5000.0
    assert "history" in data["preferences"]["interests"]
    assert data["source"] in ["heuristic_nlp", "llm"]


def test_api_extract_preferences_validation():
    """Verify validation rejects empty or too short text."""
    response = client.post(
        "/api/ai/extract-preferences",
        json={"text": ""},
    )
    assert response.status_code == 422


def test_api_chat_endpoint_general_qa():
    """Verify POST /api/ai/chat endpoint for historical questions."""
    response = client.post(
        "/api/ai/chat",
        json={
            "message": "Tell me about Charminar and Hyderabad culture",
            "destination_hint": "Hyderabad",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert "reply" in data
    assert len(data["reply"]) > 20
    assert len(data["workflow_trace"]) > 0


def test_api_chat_endpoint_itinerary_generation():
    """Verify POST /api/ai/chat endpoint for full trip generation."""
    response = client.post(
        "/api/ai/chat",
        json={
            "message": "Plan a 2-day trip to Hyderabad for 1 person with budget 6000",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["intent"] == "plan_trip"
    assert data["extracted_preferences"]["destination"] == "Hyderabad"
    assert data["extracted_preferences"]["duration_days"] == 2
    assert data["itinerary"] is not None
    assert "Planned 2-Day Itinerary" in data["reply"]


# ==============================================================================
# 5. RESILIENCE & DETERMINISTIC REPRODUCIBILITY
# ==============================================================================

def test_resilience_missing_openai_key():
    """Verify system remains fully operational and deterministic when OPENAI_API_KEY is not set."""
    # Temporarily set API key to None
    original_key = ai_service.api_key
    ai_service.api_key = None
    ai_service._openai_client = None

    try:
        res = ai_service.extract_preferences(
            "I want a relaxed 2-day trip to Hyderabad. I like historical places and good food. My budget is ₹5,000."
        )
        assert res.source == "heuristic_nlp"
        assert res.preferences.destination == "Hyderabad"
        assert res.preferences.duration_days == 2
        assert res.preferences.budget == 5000.0
        assert res.preferences.travel_style == "relaxed"
    finally:
        ai_service.api_key = original_key
        ai_service._openai_client = None
