import { SearchPage } from "./features/search/SearchPage";

function App() {
  return (
    <div
      style={{ maxWidth: 800, margin: "2rem auto", fontFamily: "system-ui" }}
    >
      <h1>Search Demo</h1>
      <SearchPage />
    </div>
  );
}

export default App;
