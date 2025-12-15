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

    match_patterns: list[str] = Field(default_factory=list, description="Entity match patterns, e.g., ['(d:Disease)', '(s:Symptom)']")
    relationships: list[str] = Field(default_factory=list, description="Relationship patterns, e.g., ['TREATS', 'CAUSES']")
    where_clause: str | None = Field(None, description="Optional WHERE conditions")
    return_clause: str = Field("d, s", description="What to return from the query")
    limit: int | None = Field(None, description="Optional result limit")

    def __str__(self) -> str:
        """Convert the CypherQuery to a valid Cypher query string."""
        if not self.match_patterns:
            return "MATCH (n) RETURN n LIMIT 10"
        
        match_pattern = ", ".join(self.match_patterns)
        if self.relationships:
            for i, rel in enumerate(self.relationships):
                if i < len(self.match_patterns) - 1:
                    match_pattern += f"-[r{i}:{rel}]->"
        
        query = f"MATCH {match_pattern}"
        
        if self.where_clause:
            query += f" WHERE {self.where_clause}"
        
        query += f" RETURN {self.return_clause}"
        
        if self.limit:
            query += f" LIMIT {self.limit}"
        
        return query
