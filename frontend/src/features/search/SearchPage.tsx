import { useState, type FormEvent } from "react";
import { addSearchHistory, search, type SearchResult } from "../../lib/api";

export const SearchPage = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>();

  async function handleSearch(event: FormEvent) {
    event.preventDefault();

    const trimmed = query.trim();
    if (!trimmed) {
      return;
    }

    // TODO (candidate):
    // - Call the /api/search endpoint with the current query.
    // - Update `results` with the returned data.
    // - Use `loading` and `error` to reflect request state.
  }

  return (
    <div>
      <form
        onSubmit={handleSearch}
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

      {results?.length && results.length > 0 && (
        <ul>
          {results.map((r) => (
            <li key={r.document.id} style={{ marginBottom: "0.5rem" }}>
              <strong>{r.document.title}</strong> (score: {r.score.toFixed(3)})
              {r.reason && (
                <div style={{ fontSize: "0.85rem", color: "#555" }}>
                  {r.reason}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
