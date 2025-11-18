import { useEffect, useState } from "react";
import { getSearchHistory, type SearchEntry } from "../../lib/api";

interface Props {
  onSelectQuery: (query: string) => void;
}

export const RecentSearches = ({ onSelectQuery }: Props) => {
  const [entries, setEntries] = useState<SearchEntry[]>([]);
  const [error, setError] = useState<string | null>();

  useEffect(() => {
    async function loadHistory() {
      try {
        const data = await getSearchHistory();
        setEntries(data);
      } catch (err: any) {
        setError(err?.message ?? "Failed to load history");
      }
    }
    loadHistory();
  }, []);

  if (error) {
    return <div style={{ color: "red" }}>Failed to load recent searches.</div>;
  }

  if (entries.length === 0) {
    return <div>No recent searches yet.</div>;
  }

  return (
    <div>
      <h2>Recent searches</h2>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {entries.map((entry) => (
          <li key={entry.timestamp}>
            <button
              type="button"
              style={{
                all: "unset",
                cursor: "pointer",
                color: "blue",
                textDecoration: "underline",
              }}
              onClick={() => onSelectQuery(entry.query)}
            >
              {entry.query}
            </button>{" "}
            <span style={{ fontSize: "0.8rem", color: "#777" }}>
              ({new Date(entry.timestamp).toLocaleString()})
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};
