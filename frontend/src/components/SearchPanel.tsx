import { useEffect, useRef, useState } from "react";
import { searchTitles } from "../api";
import type { TitleMatch } from "../types";
import { Chip } from "./Chip";

type Mode = "book" | "vibe";

interface SearchPanelProps {
  allGenres: string[];
  allMoods: string[];
  onSubmitBook: (title: string) => void;
  onSubmitVibe: (genres: string[], moods: string[]) => void;
  onModeChange: () => void;
  loading: boolean;
}

export function SearchPanel({
  allGenres,
  allMoods,
  onSubmitBook,
  onSubmitVibe,
  onModeChange,
  loading,
}: SearchPanelProps) {
  const [mode, setMode] = useState<Mode>("book");

  function switchMode(next: Mode) {
    if (next === mode) return;
    setMode(next);
    onModeChange();
  }

  const [titleQuery, setTitleQuery] = useState("");
  const [matches, setMatches] = useState<TitleMatch[]>([]);
  const [showMatches, setShowMatches] = useState(false);
  const [highlighted, setHighlighted] = useState(-1);
  const debounceRef = useRef<number | undefined>(undefined);

  const [genres, setGenres] = useState<string[]>([]);
  const [moods, setMoods] = useState<string[]>([]);

  useEffect(() => {
    window.clearTimeout(debounceRef.current);
    if (!titleQuery.trim()) {
      setMatches([]);
      return;
    }
    debounceRef.current = window.setTimeout(async () => {
      try {
        const results = await searchTitles(titleQuery);
        setMatches(results);
        setHighlighted(-1);
      } catch {
        setMatches([]);
      }
    }, 200);
    return () => window.clearTimeout(debounceRef.current);
  }, [titleQuery]);

  function toggleGenre(g: string) {
    setGenres((prev) => (prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g]));
  }

  function toggleMood(m: string) {
    setMoods((prev) => (prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]));
  }

  function submitBook(title: string) {
    setShowMatches(false);
    setHighlighted(-1);
    setTitleQuery(title);
    onSubmitBook(title);
  }

  function handleBookFormSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (showMatches && highlighted >= 0 && matches[highlighted]) {
      submitBook(matches[highlighted].title);
    } else if (titleQuery.trim()) {
      submitBook(titleQuery.trim());
    }
  }

  function handleTitleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!showMatches || matches.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlighted((h) => (h + 1) % matches.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlighted((h) => (h <= 0 ? matches.length - 1 : h - 1));
    } else if (e.key === "Escape") {
      setShowMatches(false);
    }
  }

  function handleVibeSubmit() {
    onSubmitVibe(genres, moods);
  }

  return (
    <section className="search-panel" aria-label="Search for recommendations">
      <div className="mode-toggle" role="tablist" aria-label="Search mode">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "book"}
          className={`mode-toggle__btn${mode === "book" ? " mode-toggle__btn--active" : ""}`}
          onClick={() => switchMode("book")}
        >
          A book I loved
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "vibe"}
          className={`mode-toggle__btn${mode === "vibe" ? " mode-toggle__btn--active" : ""}`}
          onClick={() => switchMode("vibe")}
        >
          A genre + mood
        </button>
      </div>

      {mode === "book" ? (
        <form className="book-form" onSubmit={handleBookFormSubmit}>
          <div className="autocomplete">
            <input
              type="text"
              inputMode="text"
              autoComplete="off"
              placeholder="Type something......"
              value={titleQuery}
              onChange={(e) => {
                setTitleQuery(e.target.value);
                setShowMatches(true);
              }}
              onFocus={() => setShowMatches(true)}
              onBlur={() => window.setTimeout(() => setShowMatches(false), 120)}
              onKeyDown={handleTitleKeyDown}
              aria-label="Book title"
              aria-autocomplete="list"
              aria-expanded={showMatches && matches.length > 0}
              aria-activedescendant={highlighted >= 0 ? `title-match-${highlighted}` : undefined}
              role="combobox"
            />
            {showMatches && matches.length > 0 && (
              <ul className="autocomplete__list" role="listbox">
                {matches.map((m, i) => (
                  <li key={m.id} role="presentation">
                    <button
                      type="button"
                      id={`title-match-${i}`}
                      role="option"
                      aria-selected={i === highlighted}
                      data-highlighted={i === highlighted}
                      onMouseEnter={() => setHighlighted(i)}
                      onClick={() => submitBook(m.title)}
                    >
                      <span className="autocomplete__title">{m.title}</span>
                      <span className="autocomplete__author">{m.author}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <button type="submit" className="btn-primary" disabled={loading || !titleQuery.trim()}>
            {loading && <span className="btn-primary__spinner" aria-hidden="true" />}
            {loading ? "Pulling books…" : "Search for recommendations"}
          </button>
        </form>
      ) : (
        <div className="vibe-form">
          <div className="tag-group">
            <span className="tag-group__label">Genre</span>
            <div className="tag-group__chips">
              {allGenres.map((g) => (
                <Chip key={g} label={g} active={genres.includes(g)} onToggle={() => toggleGenre(g)} />
              ))}
            </div>
          </div>
          <div className="tag-group">
            <span className="tag-group__label">Mood</span>
            <div className="tag-group__chips">
              {allMoods.map((m) => (
                <Chip key={m} label={m} active={moods.includes(m)} onToggle={() => toggleMood(m)} />
              ))}
            </div>
          </div>
          <button
            type="button"
            className="btn-primary"
            disabled={loading || (genres.length === 0 && moods.length === 0)}
            onClick={handleVibeSubmit}
          >
            {loading && <span className="btn-primary__spinner" aria-hidden="true" />}
            {loading ? "Pulling books…" : "Search for recommendations"}
          </button>
        </div>
      )}
    </section>
  );
}