from typing import Any, Dict, List, Optional

try:
    from app.core.logger import logger
    from app.rag.vector_store import vector_store
    from app.schemas.ai import SourceDocument
except ImportError:
    from backend.app.core.logger import logger
    from backend.app.rag.vector_store import vector_store
    from backend.app.schemas.ai import SourceDocument


class SemanticRetriever:
    """Retrieval component responsible for context-grounded retrieval and fact synthesis."""

    def __init__(self, store=vector_store):
        self.store = store

    def retrieve(
        self,
        query: str,
        destination: Optional[str] = None,
        top_k: int = 3,
    ) -> List[SourceDocument]:
        """Retrieve relevant knowledge base chunks matching the user inquiry."""
        raw_results = self.store.search(query=query, destination=destination, top_k=top_k)

        source_docs: List[SourceDocument] = []
        for r in raw_results:
            source_docs.append(
                SourceDocument(
                    title=r["title"],
                    source=r["source"],
                    category=r["category"],
                    destination=r["destination"],
                    content=r["content"],
                    relevance_score=r.get("relevance_score"),
                )
            )

        return source_docs

    def generate_grounded_answer(
        self,
        query: str,
        sources: List[SourceDocument],
    ) -> str:
        """Synthesize a context-grounded, fact-based answer citing retrieved sources.

        Adheres strictly to the AI Rule:
        - Never invent facts.
        - Clearly distinguish retrieved verified facts from AI suggestions.
        - Include source attribution.
        """
        if not sources:
            return (
                "I searched the TravelSenseAI tourism knowledge base, but could not find verified "
                "historical or cultural records directly answering your specific query. "
                "For live attraction schedules and route calculations, please use our interactive itinerary tools."
            )

        citations = []
        snippets = []
        for s in sources:
            snippets.append(f"• **{s.title}** ({s.source}):\n  \"{s.content}\"")
            if s.source not in citations:
                citations.append(f"{s.source}")

        sources_summary = ", ".join(citations)

        return (
            f"### Verified Knowledge Base Facts:\n\n"
            f"{chr(10).join(snippets)}\n\n"
            f"> **Source Grounding**: Verified against *{sources_summary}*. "
            f"AI suggestions are strictly separated from historical and factual archives."
        )


retriever = SemanticRetriever()

