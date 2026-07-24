export interface BookResult {
  id: string;
  title: string;
  author: string;
  genres: string[];
  moods: string[];
  matched_genres: string[];
  matched_moods: string[];
  tag_score: number;
  rationale: string;
  rationale_source: "llm" | "tag-match" | "seed" | "browse";
  cover_url: string | null;
  first_publish_year: number | null;
}

export interface RecommendResponse {
  seed_resolved_title: string | null;
  seed_book: BookResult | null;
  used_llm_rerank: boolean;
  results: BookResult[];
}

export interface CatalogResponse {
  genres: string[];
  moods: string[];
  titles: string[];
}

export interface TitleMatch {
  id: string;
  title: string;
  author: string;
}

export interface RandomBooksResponse {
  results: BookResult[];
}