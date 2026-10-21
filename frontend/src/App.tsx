import { useEffect, useState } from "react";
import { fetchCatalog, fetchRandomBooks, fetchRecommendations } from "./api";
import { BookCard } from "./components/BookCard";
import { BookGrid } from "./components/BookGrid";
import { Footer } from "./components/Footer";
import { SavedShelf } from "./components/SavedShelf";
import { SearchPanel } from "./components/SearchPanel";
import type { BookResult } from "./types";
import { useSavedBooks } from "./useSavedBooks";

export default function App() {
  const [allGenres, setAllGenres] = useState<string[]>([]);
  const [allMoods, setAllMoods] = useState<string[]>([]);
  const [randomBooks, setRandomBooks] = useState<BookResult[]>([]);

  const [results, setResults] = useState<BookResult[]>([]);
  const [seedTitle, setSeedTitle] = useState<string | null>(null);
  const [seedBook, setSeedBook] = useState<BookResult | null>(null);
  const [usedLlm, setUsedLlm] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const { saved, isSaved, toggleSaved, removeSaved } = useSavedBooks();

  useEffect(() => {
    fetchCatalog()
      .then((c) => {
        setAllGenres(c.genres);
        setAllMoods(c.moods);
      })
      .catch(() => {
        // Catalog is only needed to populate the vibe-mode chip list —
        // the book-title mode still works via free-text + autocomplete.
      });

    fetchRandomBooks(5)
      .then(setRandomBooks)
      .catch(() => {
        // The landing picks are a nice-to-have — search still works without them.
      });
  }, []);

  function resetResults() {
    setResults([]);
    setSeedTitle(null);
    setSeedBook(null);
    setError(null);
    setHasSearched(false);
  }

  async function runSearch(params: { seedTitle?: string; genres?: string[]; moods?: string[] }) {
    setLoading(true);
    setError(null);
    setHasSearched(true);
    try {
      const res = await fetchRecommendations({ ...params, limit: 6 });
      setResults(res.results);
      setSeedTitle(res.seed_resolved_title);
      setSeedBook(res.seed_book);
      setUsedLlm(res.used_llm_rerank);
    } catch (err) {
      setResults([]);
      setSeedBook(null);
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <nav className="nav">
        <div className="nav__inner">
          <span className="nav__brand">
            <span className="nav__logo" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="15" height="15">
                <path
                  fill="#fff"
                  d="M5 4.5A1.5 1.5 0 0 1 6.5 3H18a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H7a1 1 0 0 0 0 2h11a1 1 0 1 1 0 2H7a3 3 0 0 1-3-3V4.5Z"
                />
              </svg>
            </span>
            Book Recommender
          </span>
          <a
            className="nav__link"
            href="https://github.com/bhawnauk"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub ↗
          </a>
        </div>
      </nav>

      <div className="app">
        <header className="app__header">
          <p className="app__eyebrow">Tone-aware recommendations</p>
          <h1>Tell me what you loved. I'll find what you will love.</h1>
          <p className="app__lede">
            A star rating alone can't tell two five-star thrillers apart. This tool looks past
            the score to what actually made a book work — its tone, pacing, structure — and turns
            that into a short, well-reasoned shortlist based on what you loved.
          </p>
        </header>

        <main>
          <div className="app__controls">
            <SearchPanel
              allGenres={allGenres}
              allMoods={allMoods}
              onSubmitBook={(title) => runSearch({ seedTitle: title })}
              onSubmitVibe={(genres, moods) => runSearch({ genres, moods })}
              onModeChange={resetResults}
              loading={loading}
            />
            <SavedShelf saved={saved} onRemove={removeSaved} />
          </div>

          {error && <p className="app__error">{error}</p>}

          {!error && hasSearched && !loading && results.length === 0 && (
            <p className="app__empty">
              No matches on the shelf for that. This runs on a small curated catalog rather
              than a full book database — try a different title, or switch to genre + mood.
            </p>
          )}

          {!hasSearched && randomBooks.length > 0 && (
            <div className="discover-section">
              <p className="section-label">Not sure where to start? A few picks</p>
              <BookGrid books={randomBooks} isSaved={isSaved} onToggleSave={toggleSaved} />
            </div>
          )}

          {results.length > 0 && (
            <div className={`app__results${loading ? " app__results--loading" : ""}`}>
              {seedBook && (
                <section className="seed-section">
                  <p className="section-label">The book you loved</p>
                  <div className="book-grid">
                    <BookCard
                      book={seedBook}
                      saved={isSaved(seedBook.id)}
                      onToggleSave={() => toggleSaved(seedBook)}
                    />
                  </div>
                </section>
              )}

              <div className="app__results-meta">
                <span>
                  {seedTitle ? (
                    <>
                      Because you loved <strong>{seedTitle}</strong>
                    </>
                  ) : (
                    "Matching your mood"
                  )}
                </span>
                <span className={`llm-indicator${usedLlm ? " llm-indicator--on" : ""}`}>
                  {usedLlm ? "Reasoned by local LLM" : "Tag-matched"}
                </span>
              </div>

              <BookGrid books={results} isSaved={isSaved} onToggleSave={toggleSaved} />
            </div>
          )}
        </main>

        <Footer />
      </div>
    </>
  );
}