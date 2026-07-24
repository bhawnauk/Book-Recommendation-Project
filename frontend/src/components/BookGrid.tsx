import type { BookResult } from "../types";
import { BookCard } from "./BookCard";

interface BookGridProps {
  books: BookResult[];
  isSaved: (id: string) => boolean;
  onToggleSave: (book: BookResult) => void;
}

export function BookGrid({ books, isSaved, onToggleSave }: BookGridProps) {
  if (books.length === 0) return null;
  return (
    <div className="book-grid">
      {books.map((b) => (
        <BookCard key={b.id} book={b} saved={isSaved(b.id)} onToggleSave={() => onToggleSave(b)} />
      ))}
    </div>
  );
}
