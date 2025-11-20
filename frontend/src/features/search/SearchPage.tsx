import { type FormEvent, useState } from "react";
import type { SearchResult } from "../../lib/api";
import { search as apiSearch } from "../../lib/api";

export const SearchPage = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>();

  async function handleSearch(rawQuery: string) {
    const trimmed = rawQuery.trim();
    if (!trimmed) return;

    // Keep input in sync when triggered from RecentSearches
    setQuery(rawQuery);

    setLoading(true);
    setError(null);
    try {
      const res = await apiSearch(trimmed);
      setResults(res as unknown as SearchResult[]);
    } catch (err: any) {
      setError(err?.message ?? "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    void handleSearch(query);
  };

  return (
    <div>
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search documents..."
          style={{ flex: 1, padding: "0.5rem" }}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && (
        <div style={{ color: "red", marginBottom: "0.5rem" }}>{error}</div>
      )}

      {results?.length === 0 && !loading && !error && (
        <div>No results yet. Try searching for something.</div>
      )}

      {results && results.length > 0 && (
        <ul>
          {results.map((r, idx) => {
            const doc: any = r.document as any;
            const id = doc?.metadata?.id ?? doc?.id ?? idx;
            const title = doc?.metadata?.title ?? doc?.title ?? "(no title)";
            const body = doc?.page_content ?? doc?.body ?? "";
            return (
              <li key={String(id)} style={{ marginBottom: "0.5rem" }}>
                <strong>{title}</strong> (score: {r.score.toFixed(3)})
                <div style={{ fontSize: "0.9rem", color: "#333" }}>
                  {body}
                </div>
                {r.reason && (
                  <div style={{ fontSize: "0.85rem", color: "#555" }}>
                    {r.reason}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};
