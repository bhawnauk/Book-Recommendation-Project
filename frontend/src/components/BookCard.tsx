import { useEffect, useState } from "react";
import { amazonSearchUrl } from "../amazon";
import type { BookResult } from "../types";

interface BookCardProps {
  book: BookResult;
  saved: boolean;
  onToggleSave: () => void;
}

const RATIONALE_LABEL: Record<BookResult["rationale_source"], string> = {
  llm: "Why this fits",
  "tag-match": "What makes it work",
  seed: "Why you loved it",
  browse: "Why it's loved",
};

export function BookCard({ book, saved, onToggleSave }: BookCardProps) {
  const [coverFailed, setCoverFailed] = useState(false);

  useEffect(() => {
    setCoverFailed(false);
  }, [book.cover_url]);

  return (
    <article className="book-card">
      <header className="book-card__head">
        <div className="book-card__cover">
          {book.cover_url && !coverFailed ? (
            <img
              src={book.cover_url}
              alt={`Cover of ${book.title}`}
              onError={() => setCoverFailed(true)}
            />
          ) : (
            <div className="book-card__cover-placeholder" aria-hidden="true">
              <span>{book.title.slice(0, 1)}</span>
            </div>
          )}
        </div>
        <div>
          <h3>{book.title}</h3>
          <p className="book-card__author">
            {book.author}
            {book.first_publish_year ? ` · ${book.first_publish_year}` : ""}
          </p>
        </div>
      </header>

      <p className="book-card__rationale">
        <span className={`rationale-badge rationale-badge--${book.rationale_source}`}>
          {RATIONALE_LABEL[book.rationale_source]}
        </span>
        {book.rationale}
      </p>

      <div className="book-card__tags">
        {book.genres.map((g) => (
          <span
            key={g}
            className={`tag${book.matched_genres.includes(g) ? " tag--matched" : ""}`}
          >
            {g}
          </span>
        ))}
        {book.moods.map((m) => (
          <span
            key={m}
            className={`tag${book.matched_moods.includes(m) ? " tag--matched" : ""}`}
          >
            {m}
          </span>
        ))}
      </div>

      <div className="book-card__actions">
        <button type="button" className="btn-save" onClick={onToggleSave} aria-pressed={saved}>
          {saved ? "Saved ✓" : "Save to shelf"}
        </button>
        <a
          className="btn-amazon"
          href={amazonSearchUrl(book.title, book.author)}
          target="_blank"
          rel="noopener noreferrer"
        >
          View on Amazon <span aria-hidden="true">↗</span>
        </a>
      </div>
    </article>
  );
}
