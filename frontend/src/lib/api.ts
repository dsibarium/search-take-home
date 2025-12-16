export type SearchDocumentMetadata = {
  id: number;
  title: string;
  // Allow additional metadata fields without losing type safety.
  [key: string]: unknown;
};

export type SearchDocument = {
  page_content: string;
  metadata: SearchDocumentMetadata;
};

export type SearchResult = {
  document: SearchDocument;
  score: number;
  reason?: string;
};

export class SearchError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "SearchError";
    this.status = status;
  }
}

/**
 * Perform a search request against the backend.
 *
 * TODO (candidate):
 * - Call the `/api/search` endpoint via `fetch`.
 * - Send `{ query, top_k: topK }` as a JSON body.
 * - On non-OK responses, throw a `SearchError` with a helpful message and
 *   the HTTP status code.
 * - Parse and return the JSON response typed as `SearchResult[]`.
 */
export async function search(query: string, topK = 5): Promise<SearchResult[]> {
  const body = { query, top_k: topK };

  const res = await fetch(`/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const msg = text || `Search request failed with status ${res.status}`;
    throw new SearchError(msg, res.status);
  }

  const data = (await res.json()) as SearchResult[];
  return data;
}
