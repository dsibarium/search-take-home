from fastapi import APIRouter, HTTPException

from .data import DOCUMENTS  # noqa: F401
from .models import SearchEntry, SearchRequest, SearchResult
from .scoring import search_documents

router = APIRouter(prefix="/search", tags=["search"])
SEARCH_HISTORY: list[SearchEntry] = []


@router.post("", response_model=list[SearchResult])
async def search(request: SearchRequest) -> list[SearchResult]:
    """
    Search over the in-memory DOCUMENTS collection.
    - Implement simple ranking logic over DOCUMENTS based on `request.query`.
    - Return the top `request.top_k` results, sorted by score (highest first).

    Focus on clear, readable, and well-structured code.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    # Run the search over our in-memory documents
    results = search_documents(query, DOCUMENTS, top_k=request.top_k)

    # Record search to history (non-blocking)
    try:
        SEARCH_HISTORY.append(
            SearchEntry(query=query, timestamp=__import__("datetime").datetime.now())
        )
    except Exception:
        # Do not fail the request for a history write error
        pass

    return results
