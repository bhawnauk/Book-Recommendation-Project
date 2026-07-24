import type { CatalogResponse, RandomBooksResponse, RecommendResponse, TitleMatch } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON, keep statusText
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function fetchCatalog(): Promise<CatalogResponse> {
  const res = await fetch(`${API_BASE_URL}/catalog`);
  return handle<CatalogResponse>(res);
}

export async function searchTitles(query: string): Promise<TitleMatch[]> {
  if (!query.trim()) return [];
  const res = await fetch(`${API_BASE_URL}/search-titles?q=${encodeURIComponent(query)}`);
  const data = await handle<{ matches: TitleMatch[] }>(res);
  return data.matches;
}

export async function fetchRandomBooks(limit = 5) {
  const res = await fetch(`${API_BASE_URL}/random-books?limit=${limit}`);
  const data = await handle<RandomBooksResponse>(res);
  return data.results;
}

export interface RecommendParams {
  seedTitle?: string;
  genres?: string[];
  moods?: string[];
  limit?: number;
}

export async function fetchRecommendations(params: RecommendParams): Promise<RecommendResponse> {
  const res = await fetch(`${API_BASE_URL}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      seed_title: params.seedTitle || undefined,
      genres: params.genres && params.genres.length ? params.genres : undefined,
      moods: params.moods && params.moods.length ? params.moods : undefined,
      limit: params.limit ?? 6,
    }),
  });
  return handle<RecommendResponse>(res);
}