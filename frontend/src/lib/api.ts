export type SearchResult = {
  document: {
    id: string;
    title: string;
    body: string;
  };
  score: number;
  reason?: string;
};

export async function search(query: string, topK = 5): Promise<SearchResult[]> {
  const response = await fetch("/api/search", {
    method: "POST",
    body: JSON.stringify({ query, top_k: topK }),
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Search failed with status ${response.status}`);
  }

  return response.json();
}
