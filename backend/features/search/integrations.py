from functools import lru_cache
import math
from typing import Optional

import numpy as np
from langchain_core.documents import Document

from .models import SearchResult, CypherQuery


def _embed_text(text: str, dim: int = 64) -> np.ndarray:
    """Deterministic pseudo-embedding based on a text hash.

    This avoids external dependencies and is deterministic for tests.
    """
    seed = abs(hash(text)) % (2 ** 32)
    rng = np.random.RandomState(seed)
    vec = rng.rand(dim).astype(np.float32)
    # normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


async def text_to_cypher(text: str) -> str:
    """Create a simple Cypher query string from free text.

    This is a small heuristic-based implementation that produces a usable Cypher
    query string without requiring an external LLM. For example, a query about
    a disease or drug will be converted into a `MATCH` + `WHERE` clause that
    checks `name` and `description` for a substring match.
    """
    t = text.strip().replace("'", "\\'")
    if not t:
        return "MATCH (n) RETURN n"

    # simple heuristics to guess entity labels
    lower = text.lower()
    if any(k in lower for k in ("disease", "symptom")):
        label = "Disease"
    elif any(k in lower for k in ("drug", "medication", "medicine")):
        label = "Drug"
    else:
        label = None

    if label:
        q = CypherQuery(match=f"(n:{label})", where=f"toLower(n.name) CONTAINS '{t.lower()}'", returns=["n"])
    else:
        q = CypherQuery(match="(n)", where=f"toLower(n.name) CONTAINS '{t.lower()}' OR toLower(n.description) CONTAINS '{t.lower()}'", returns=["n"])  # type: ignore[arg-type]

    return str(q)


class SimpleVectorStore:
    """A tiny in-memory vector store with cosine similarity search."""

    def __init__(self, documents: list[Document], dim: int = 64):
        self.documents = documents
        self.dim = dim
        self.embeddings = np.vstack([_embed_text(d.page_content or "", dim) for d in documents])

    def similarity_search(self, query: str, k: int = 5) -> list[tuple[Document, float]]:
        qvec = _embed_text(query, self.dim)
        sims = float.__array_priority__  # silence linter when not used
        # cosine similarity since vectors are normalized
        scores = np.dot(self.embeddings, qvec)
        idx = np.argsort(-scores)
        results: list[tuple[Document, float]] = []
        for i in idx[:k]:
            results.append((self.documents[int(i)], float(scores[int(i)])))
        return results


@lru_cache()
def load_FAISS(documents: tuple[Document, ...]) -> SimpleVectorStore:
    """Return a SimpleVectorStore built from DOCUMENTS.

    The function accepts a tuple so it can be safely cached via `lru_cache`.
    """
    return SimpleVectorStore(list(documents))


def search_knowledgegraph(cypher_query: str) -> list[SearchResult]:
    """Mock KG search: return the cypher query as a document with a strong score.

    In a real implementation this would execute the Cypher query against a graph DB.
    """
    return [
        SearchResult(document=Document(page_content=cypher_query), score=0.9, reason="kg-match")
    ]


def _merge_and_rerank(v_results: list[tuple[Document, float]], kg_results: list[SearchResult], top_k: int) -> list[SearchResult]:
    """Merge vector results and KG results, then rerank into SearchResult list.

    - Convert vector similarity (cosine in [-1,1]) to a 0-1 score.
    - Combine KG score (already 0-1) by taking max(vec, kg*0.6) to give KG some weight.
    """
    merged: dict[str, SearchResult] = {}

    for doc, raw_score in v_results:
        # raw_score is cosine in [-1,1]; map to [0,1]
        vscore = max(0.0, (raw_score + 1.0) / 2.0)
        key = (doc.page_content or "")
        merged[key] = SearchResult(document=doc, score=vscore, reason="vector")

    for kg in kg_results:
        key = (kg.document.page_content or "")
        if key in merged:
            existing = merged[key]
            combined = max(existing.score, kg.score * 0.6)
            merged[key] = SearchResult(document=existing.document, score=combined, reason="vector+kg")
        else:
            merged[key] = kg

    results = sorted(merged.values(), key=lambda r: r.score, reverse=True)
    return results[:top_k]


def search_documents(query: str, documents: list[Document], top_k: int = 10) -> list[SearchResult]:
    """Search documents using a local vector store + knowledgegraph signals.

    Steps:
    1. load the in-memory vector store
    2. run a vector similarity search
    3. convert text to a (mock) Cypher query and run KG search
    4. merge & rerank results, return top_k results
    """
    if not documents:
        return []

    store = load_FAISS(tuple(documents))
    v_results = store.similarity_search(query, k=max(10, top_k))

    cypher = ""
    try:
        # text_to_cypher is async; call synchronously via simple loop if needed
        import asyncio

        cypher = asyncio.get_event_loop().run_until_complete(text_to_cypher(query))
    except Exception:
        # fallback to a simple heuristic
        cypher = str(CypherQuery(match="(n)", where=f"toLower(n.name) CONTAINS '{query.lower()}'", returns=["n"]))

    kg_results = search_knowledgegraph(cypher)

    return _merge_and_rerank(v_results, kg_results, top_k)
