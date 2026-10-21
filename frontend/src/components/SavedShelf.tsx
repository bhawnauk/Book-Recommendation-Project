import type { BookResult } from "../types";

interface SavedShelfProps {
  saved: BookResult[];
  onRemove: (id: string) => void;
}

export function SavedShelf({ saved, onRemove }: SavedShelfProps) {
  return (
    <aside className="saved-shelf" aria-label="Your saved shortlist">
      <h2>
        Your shelf
        {saved.length > 0 && <span className="saved-shelf__count">{saved.length}</span>}
      </h2>
      {saved.length === 0 ? (
        <p className="saved-shelf__empty">
          Nothing saved yet. Books you save will collect here — a running shortlist, not a
          to-do list.
        </p>
      ) : (
        <ul className="saved-shelf__list">
          {saved.map((b) => (
            <li key={b.id}>
              <div>
                <p className="saved-shelf__title">{b.title}</p>
                <p className="saved-shelf__author">{b.author}</p>
              </div>
              <button
                type="button"
                className="saved-shelf__remove"
                onClick={() => onRemove(b.id)}
                aria-label={`Remove ${b.title} from your shelf`}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}