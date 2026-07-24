import { useCallback, useEffect, useState } from "react";
import type { BookResult } from "./types";

const STORAGE_KEY = "book-recommender:saved";

function readInitial(): BookResult[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as BookResult[]) : [];
  } catch {
    return [];
  }
}

export function useSavedBooks() {
  const [saved, setSaved] = useState<BookResult[]>(readInitial);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
    } catch {
      // storage unavailable (private browsing, quota) — fail silently,
      // the shortlist still works for the current session
    }
  }, [saved]);

  const isSaved = useCallback((id: string) => saved.some((b) => b.id === id), [saved]);

  const toggleSaved = useCallback((book: BookResult) => {
    setSaved((prev) =>
      prev.some((b) => b.id === book.id)
        ? prev.filter((b) => b.id !== book.id)
        : [...prev, book],
    );
  }, []);

  const removeSaved = useCallback((id: string) => {
    setSaved((prev) => prev.filter((b) => b.id !== id));
  }, []);

  return { saved, isSaved, toggleSaved, removeSaved };
}