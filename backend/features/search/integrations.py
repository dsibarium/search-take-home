from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from .models import SearchResult, CypherQuery

_FAISS_CACHE: FAISS | None = None


async def text_to_cypher(text: str) -> CypherQuery:
    """Convert a text query to a Cypher query.

    You should use an LangChain LLM using 'with_structured_output' to generate the Cypher query.
    Reference the docs here: https://docs.langchain.com/oss/python/langchain/structured-output#:~:text=LangChain%20automatically%20uses%20ProviderStrategy%20when%20you%20pass%20a%20schema%20type%20directly%20to%20create_agent.response_format%20and%20the%20model%20supports%20native%20structured%20output%3A

    Assume the knowledge graph has the following ontology:
    - Entities:
     - Disease
     - Symptom
     - Drug
     - Patient
    - Relationships:
     - TREATS
     - CAUSES
     - EXPERIENCING
     - SUFFERING_FROM

    You should have the model construct a Cypher query via a structured output (using JSON schema or
    Pydantic BaseModels) that can be used to query the system. If you have an API key, you may use it -
    otherwise, simply construct the LLM & assume that the the API key will be populated later.
    """
    system_prompt = """You are a Cypher query generator for a medical knowledge graph.

The knowledge graph has the following ontology:
- Entities: Disease, Symptom, Drug, Patient
- Relationships: TREATS, CAUSES, EXPERIENCING, SUFFERING_FROM

Generate a CypherQuery object based on the user's natural language query.
Use appropriate match patterns, relationships, and return clauses."""

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(CypherQuery)
    
    prompt = f"{system_prompt}\n\nUser query: {text}"
    result = await structured_llm.ainvoke(prompt)
    return result


def load_FAISS(documents: list[Document]) -> FAISS:
    """Create and return a FAISS vector store from the DOCUMENTS list."""
    global _FAISS_CACHE
    if _FAISS_CACHE is None:
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        _FAISS_CACHE = FAISS.from_documents(documents, embeddings)
    return _FAISS_CACHE


def search_knowledgegraph(cypher_query: str) -> list[SearchResult]:
    """This is a mock function that will search the knowledge graph using a cypher query."""
    return [
        SearchResult(
            document=Document(page_content=cypher_query), score=0.9, reason="test"
        )
    ]


async def search_documents(query: str, documents: list[Document], top_k: int = 5) -> list[SearchResult]:
    """Using the FAISS vector store, search for the query and return a list of SearchResults.

    After searching FAISS, you should rerank all the remaining results using your custom 'rerank_result'
    function, and removing bad results. You may add args/kwargs as needed.
    """
    vectorstore = load_FAISS(documents)
    
    cypher_query_obj = await text_to_cypher(query)
    cypher_query_str = str(cypher_query_obj)
    
    faiss_results = vectorstore.similarity_search_with_score(query, k=top_k)
    
    faiss_search_results = [
        SearchResult(
            document=doc,
            score=min(1.0, max(0.0, 1.0 - score / 2.0)),
            reason="FAISS vector search"
        )
        for doc, score in faiss_results
    ]
    
    kg_results = search_knowledgegraph(cypher_query_str)
    
    all_results = faiss_search_results + kg_results
    
    all_results.sort(key=lambda x: x.score, reverse=True)
    
    return all_results[:top_k]
