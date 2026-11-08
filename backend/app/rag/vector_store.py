import os
import uuid
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

try:
    from app.core.logger import logger
    from app.rag.document_loader import load_curated_documents
    from app.rag.embeddings import embedding_engine
    from app.rag.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    from backend.app.core.logger import logger
    from backend.app.rag.document_loader import load_curated_documents
    from backend.app.rag.embeddings import embedding_engine
    from backend.app.rag.text_splitter import RecursiveCharacterTextSplitter

COLLECTION_NAME = "travelsense_knowledge"


class ChromaVectorStore:
    """Vector database manager using ChromaDB for travel knowledge retrieval."""

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory
        if persist_directory:
            os.makedirs(persist_directory, exist_ok=True)
            self.client: ClientAPI = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client: ClientAPI = chromadb.Client()

        self.collection: Collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_engine,
            metadata={"description": "Curated TravelSenseAI Tourism Knowledge Base"},
        )
        self._ensure_initialized()

    def _ensure_initialized(self):
        """Populate vector database with curated knowledge base if empty."""
        try:
            count = self.collection.count()
            if count == 0:
                logger.info("Initializing ChromaDB with curated destination knowledge...")
                self.index_curated_knowledge()
        except Exception as e:
            logger.warning(f"Could not check or initialize Chroma collection: {e}")

    def index_curated_knowledge(self):
        """Load curated documents, chunk them, and add to vector store."""
        docs = load_curated_documents()
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

        chunks_text: List[str] = []
        chunks_meta: List[Dict[str, Any]] = []
        chunks_ids: List[str] = []

        for doc in docs:
            split_chunks = splitter.split_text(doc.content)
            for idx, chunk in enumerate(split_chunks):
                chunks_text.append(chunk)
                chunks_meta.append(
                    {
                        "title": doc.title,
                        "destination": doc.destination,
                        "category": doc.category,
                        "source": doc.source,
                        "chunk_index": idx,
                    }
                )
                chunks_ids.append(f"{doc.destination}_{doc.category}_{uuid.uuid4().hex[:8]}")

        if chunks_text:
            self.collection.add(
                documents=chunks_text,
                metadatas=chunks_meta,
                ids=chunks_ids,
            )
            logger.info(f"Indexed {len(chunks_text)} chunks into ChromaDB '{COLLECTION_NAME}'.")

    def search(
        self,
        query: str,
        destination: Optional[str] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Perform semantic similarity search with optional destination filtering."""
        where_filter = None
        if destination and destination.strip():
            where_filter = {"destination": destination.strip()}

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.warning(f"Chroma query with filter failed, retrying without filter: {e}")
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

        output: List[Dict[str, Any]] = []
        if not results or not results.get("documents"):
            return output

        documents_list = results["documents"][0]
        metadatas_list = results["metadatas"][0]
        distances_list = results.get("distances", [[]])[0]

        for i, text in enumerate(documents_list):
            meta = metadatas_list[i] if i < len(metadatas_list) else {}
            dist = distances_list[i] if i < len(distances_list) else 0.0
            relevance = round(max(0.0, 1.0 - (dist / 2.0)), 3)

            output.append(
                {
                    "content": text,
                    "title": meta.get("title", "Destination Fact"),
                    "destination": meta.get("destination", "General"),
                    "category": meta.get("category", "info"),
                    "source": meta.get("source", "TravelSenseAI Knowledge Base"),
                    "relevance_score": relevance,
                }
            )

        return output


vector_store = ChromaVectorStore()

