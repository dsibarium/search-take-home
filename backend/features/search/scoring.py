import os
import re
from pathlib import Path
from typing import List
import typing as t
import uuid

import numpy as np
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from uuid import uuid4
import faiss

from .models import SearchResult


load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set in environment. Add it to .env or env vars.")

# Initialize embeddings using LangChain's OpenAIEmbeddings
# This automatically picks up OPENAI_API_KEY from environment
embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

# Path to persist FAISS index to disk
INDEX_DIR = Path(__file__).resolve().parent / ".faiss_index"
INDEX_DIR.mkdir(exist_ok=True)
INDEX_PATH = INDEX_DIR / "documents_index"

# Global cache for FAISS vector store
_cached_vector_store = None
_cached_doc_ids = None

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def rerank_result(query: str, document: Document) -> float:
    """Simple reranker based on token overlap and title boosts.

    Returns a score in 0..1 where higher is better.
    """
    q_tokens = set(_tokens(query))
    content = (getattr(document, "page_content", "") or "")
    title = str(document.metadata.get("title") if getattr(document, "metadata", None) else "")

    doc_tokens = set(_tokens(title + " " + content))
    if not doc_tokens or not q_tokens:
        return 0.0

    overlap = len(q_tokens & doc_tokens) / max(1, len(q_tokens))

    # Strong lexical boost for short queries when token(s) appear in title/content.
    # This helps single-word queries (e.g., "docker") surface documents that explicitly contain the term.
    short_query_boost = 0.0
    if len(q_tokens) <= 2 and any(t in doc_tokens for t in q_tokens):
        # make this a decisive boost for short queries
        short_query_boost = 0.7

    title_boost = 0.25 if title and query.lower() in title.lower() else 0.0

    return float(min(1.0, overlap * 0.5 + title_boost + short_query_boost))


def load_FAISS(documents: List[Document]) -> FAISS:
    """Build and return a FAISS vector store from documents using LangChain.

    Uses LangChain's FAISS wrapper with OpenAI embeddings.
    Saves index to disk to avoid re-embedding on server restart.
    """
    global _cached_vector_store, _cached_doc_ids

    # Simple cache: if document objects haven't changed, reuse the cached vector store
    doc_ids = tuple(id(d) for d in documents)
    if _cached_vector_store is not None and _cached_doc_ids == doc_ids:
        print("[CACHE HIT] Using in-memory FAISS index")
        return _cached_vector_store

    # Try to load from disk first (avoids API calls if documents unchanged)
    if INDEX_PATH.exists():
        try:
            print(f"[DISK LOAD] Loading FAISS index from {INDEX_PATH}")
            vector_store = FAISS.load_local(
                str(INDEX_PATH), embeddings_model, allow_dangerous_deserialization=True
            )
            # Cache it in memory
            _cached_vector_store = vector_store
            _cached_doc_ids = doc_ids
            return vector_store
        except Exception as e:
            print(f"[DISK LOAD FAILED] {e}. Rebuilding index from scratch.")

    # Build FAISS index from documents (calls OpenAI API)
    print("[API CALL] Creating embeddings via OpenAI API...")

    # Build a faiss IndexFlatL2 with the embedding dimension
    dim = len(embeddings_model.embed_query("hello world"))
    index = faiss.IndexFlatL2(dim)

    # Create a LangChain FAISS wrapper with an in-memory docstore
    vector_store = FAISS(
        embedding_function=embeddings_model,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
    )

    # Add documents with generated UUIDs
    ids = [str(uuid4()) for _ in documents]
    vector_store.add_documents(documents=documents, ids=ids)

    # Save to disk for next time
    try:
        print(f"[DISK SAVE] Saving FAISS index to {INDEX_PATH}")
        vector_store.save_local(str(INDEX_PATH))
    except Exception as e:
        print(f"[DISK SAVE FAILED] {e}. Index will be rebuilt on next restart.")

    # Cache for next call
    _cached_vector_store = vector_store
    _cached_doc_ids = doc_ids

    return vector_store


def search_documents(query: str, documents: List[Document], top_k: int = 5) -> List[SearchResult]:
    """Search using FAISS + OpenAI embeddings, then rerank with `rerank_result`.

    Returns up to `top_k` SearchResult ordered by score desc.
    """
    if not query or not documents: 
        return []

    # Load or retrieve cached FAISS index
    vector_store = load_FAISS(documents)

    vs = load_FAISS(documents)
    # expand candidate window to give reranker more material to work with
    candidate_window = max(top_k * 5, 10)
    candidates = vs.similarity_search_with_score(query, k=candidate_window)

    results: t.List[SearchResult] = []
    seen_ids: t.Set[str] = set()
    def _doc_uid(d: Document) -> str:
        # Prefer the original metadata id when available (stable across loads),
        # otherwise fall back to `doc.id` (e.g. FAISS-assigned UUID) or a new uuid.
        return str(d.metadata.get("id") or getattr(d, "id", None) or uuid.uuid4())

    for doc, sim_score in candidates:
        rr = rerank_result(query, doc)
        # sim_score from FAISS is a distance; smaller is better, so invert
        semantic = 1.0 / (1.0 + float(sim_score))
        final_score = 0.6 * semantic + 0.4 * rr
        results.append(SearchResult(document=doc, score=final_score, reason=None))
        seen_ids.add(_doc_uid(doc))

    # Lexical promotion: ensure any document that explicitly contains the
    # query tokens (title or content) is promoted into top_k results.
    q_low = query.lower()
    q_tokens = set(re.findall(r"\w+", q_low))
    promoted: t.List[SearchResult] = []
    for doc in documents:
        if _doc_uid(doc) in seen_ids:
            continue
        full_text = f"{doc.metadata.get('title','')} {doc.page_content}".lower()
        if any(tk in full_text for tk in q_tokens):
            # Give a clear promotion score and explain reason
            promoted.append(SearchResult(document=doc, score=1.5, reason="lexical_match"))

    # Merge promoted docs first, then FAISS+rerranked results, deduping
    merged: t.List[SearchResult] = []
    added_ids: t.Set[str] = set()
    for r in promoted + results:
        doc_uid = _doc_uid(r.document)
        if doc_uid in added_ids:
            continue
        merged.append(r)
        added_ids.add(doc_uid)

    # final sort and truncate
    merged.sort(key=lambda r: r.score, reverse=True)
    return merged[:top_k]
