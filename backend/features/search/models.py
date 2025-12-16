from datetime import datetime

from langchain_core.documents import Document
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    document: Document
    score: float = Field(..., ge=0)
    reason: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=50)


class SearchEntry(BaseModel):
    query: str = Field(..., min_length=1)
    timestamp: datetime


class CypherQuery(BaseModel):
    """Fields that can be converted to a Cypher Query in natural language."""
    # A simple, minimal representation that can be converted to a Cypher string.
    # This is intentionally small and easy to construct from natural language.
    match: str | None = Field(None, description="The MATCH pattern, e.g. '(n:Drug)'")
    where: str | None = Field(None, description="WHERE clause (without the 'WHERE' keyword)")
    returns: list[str] | None = Field(None, description="List of return expressions")

    def __str__(self) -> str:
        parts: list[str] = []
        if self.match:
            parts.append(f"MATCH {self.match}")
        else:
            parts.append("MATCH (n)")

        if self.where:
            parts.append(f"WHERE {self.where}")

        if self.returns:
            parts.append(f"RETURN {', '.join(self.returns)}")
        else:
            parts.append("RETURN n")

        return " ".join(parts)
