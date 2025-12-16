export type SearchQuery = {
  /** Raw query string entered by the user. */
  query: string;
  /** Unix timestamp in milliseconds when the query was executed. */
  timestamp: number;
};

export type SearchHistory = SearchQuery[];

export type AddToHistoryOptions = {
  /**
   * Maximum number of entries to keep.
   * Defaults to 10 if not provided.
   */
  maxEntries?: number;
};

/**
 * Add a new query to the existing history and return a new history array.
 *
 * TODO (candidate):
 * - Ignore queries that are empty or only whitespace.
 * - Add the new query as the most recent entry with the current timestamp.
 * - Avoid duplicate *adjacent* queries (if the last query has the same text,
 *   update its timestamp instead of adding a new entry).
 * - Trim the history so it never exceeds `maxEntries` (default 10).
 * - Do not mutate the `history` array; always return a new one.
 */
export function addToHistory(
  history: SearchHistory,
  query: string,
  options: AddToHistoryOptions = {},
): SearchHistory {
  const maxEntries = options.maxEntries ?? 10;
  const trimmed = query.trim();
  if (!trimmed) return [...history];

  const now = Date.now();

  // history is treated as most-recent-first. Do not mutate input.
  const copy = history.slice();

  if (copy.length > 0 && copy[0].query === trimmed) {
    // update timestamp of the most recent entry
    const updated: SearchQuery = { query: trimmed, timestamp: now };
    const newHist = [updated, ...copy.slice(1)];
    return newHist.slice(0, maxEntries);
  }

  const newEntry: SearchQuery = { query: trimmed, timestamp: now };
  const newHist = [newEntry, ...copy];
  return newHist.slice(0, maxEntries);
}

/**
 * Return a list of recent query strings in most-recent-first order.
 *
 * TODO (candidate):
 * - Use the provided `history` array (do not mutate it).
 * - Return only the `query` strings, ordered from newest to oldest.
 * - Optionally deduplicate consecutive identical strings if your
 *   `addToHistory` implementation does not already enforce this.
 */
export function getRecentQueries(history: SearchHistory): string[] {
  // Return query strings in most-recent-first order without mutating input.
  return history.map((h) => h.query);
}

