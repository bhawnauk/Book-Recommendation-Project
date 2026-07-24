from typing import List, Optional

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    seed_title: Optional[str] = Field(default=None, description="A book title the reader loved")
    genres: Optional[List[str]] = Field(default=None, description="Desired genre(s)")
    moods: Optional[List[str]] = Field(default=None, description="Desired mood(s)")
    limit: int = Field(default=6, ge=1, le=12)


class BookResult(BaseModel):
    id: str
    title: str
    author: str
    genres: List[str]
    moods: List[str]
    matched_genres: List[str]
    matched_moods: List[str]
    tag_score: float
    rationale: str
    rationale_source: str  # "llm", "tag-match", "seed", or "browse"
    cover_url: Optional[str] = None
    first_publish_year: Optional[int] = None


class RecommendResponse(BaseModel):
    seed_resolved_title: Optional[str] = None
    seed_book: Optional[BookResult] = None
    used_llm_rerank: bool
    results: List[BookResult]


class CatalogResponse(BaseModel):
    genres: List[str]
    moods: List[str]
    titles: List[str]


class RandomBooksResponse(BaseModel):
    results: List[BookResult]