## Take-home overview

Time-box to about one hour. Split the work so the candidate can discuss search quality with the ML reviewer and API/frontend integration with the SWE reviewer.

### What the candidate does async
- Implement `search` in `backend/features/search/search_router.py`.
- Implement the UI logic in `frontend/src/features/search/SearchPage.tsx` to call the search API and render results.

### What you pair on live
- Implement recent search history endpoints in `backend/features/search/search_router.py` (see `SEARCH_HISTORY` and the TODOs on `/history` routes).
- Wire up the frontend to show usable history via `RecentSearches.tsx` if needed.

### How to run
- Backend: `uvicorn backend.main:app --reload`
- Frontend: `npm install` then `npm run dev`

Keep scope light; in-memory storage is fine and no external services should be required.
