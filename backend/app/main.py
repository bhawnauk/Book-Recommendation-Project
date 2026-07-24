import os
import random
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .data import ALL_GENRES, ALL_MOODS, BOOKS, find_by_title
from .llm_rerank import rerank
from .models import (
    BookResult,
    CatalogResponse,
    RandomBooksResponse,
    RecommendRequest,
    RecommendResponse,
)
from .similarity import recommend_from_book, recommend_from_tags
load_dotenv()

app = FastAPI(
    title="Book Recommender API",
    description=(
        "Recommends books by what actually made a book work "
        "(mood, tone, structure) rather than just genre tags."
    ),
    version="0.1.0",
)

allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    return {"status": "ok", "catalog_size": len(BOOKS)}


@router.get("/catalog", response_model=CatalogResponse)
async def catalog():
    return CatalogResponse(
        genres=ALL_GENRES,
        moods=ALL_MOODS,
        titles=sorted(b["title"] for b in BOOKS),
    )


@router.get("/search-titles")
async def search_titles(q: str):
    matches = find_by_title(q)
    return {"matches": [{"id": b["id"], "title": b["title"], "author": b["author"]} for b in matches[:8]]}


def _to_seed_result(book: dict) -> BookResult:
    return BookResult(
        id=book["id"],
        title=book["title"],
        author=book["author"],
        genres=book["genres"],
        moods=book["moods"],
        matched_genres=book["genres"],
        matched_moods=book["moods"],
        tag_score=1.0,
        rationale=book["why_it_works"],
        rationale_source="seed",
        cover_url=book.get("cover_url"),
        first_publish_year=book.get("first_publish_year"),
    )


def _to_browse_result(book: dict) -> BookResult:
    return BookResult(
        id=book["id"],
        title=book["title"],
        author=book["author"],
        genres=book["genres"],
        moods=book["moods"],
        matched_genres=[],
        matched_moods=[],
        tag_score=0.0,
        rationale=book["why_it_works"],
        rationale_source="browse",
        cover_url=book.get("cover_url"),
        first_publish_year=book.get("first_publish_year"),
    )


@router.get("/random-books", response_model=RandomBooksResponse)
async def random_books(limit: int = 5):
    limit = max(1, min(limit, len(BOOKS)))
    sample = random.sample(BOOKS, limit)
    return RandomBooksResponse(results=[_to_browse_result(b) for b in sample])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    seed_book = None
    scored = []

    if req.seed_title:
        matches = find_by_title(req.seed_title)
        if not matches:
            raise HTTPException(
                status_code=404,
                detail=(
                    f'No catalog match for "{req.seed_title}". This demo runs on a '
                    "curated seed catalog rather than a full book database — "
                    "try /catalog to see available titles."
                ),
            )
        seed_book = matches[0]
        scored = recommend_from_book(seed_book["id"], limit=max(req.limit * 2, req.limit))
    elif req.genres or req.moods:
        scored = recommend_from_tags(req.genres, req.moods, limit=max(req.limit * 2, req.limit))
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either seed_title, or at least one of genres/moods.",
        )

    seed_result = _to_seed_result(seed_book) if seed_book else None

    if not scored:
        return RecommendResponse(
            seed_resolved_title=seed_book["title"] if seed_book else None,
            seed_book=seed_result,
            used_llm_rerank=False,
            results=[],
        )

    reranked = await rerank(scored, seed_book, req.genres or [], req.moods or [])
    score_by_id = {s.book["id"]: s for s in scored}

    used_llm = reranked is not None
    if used_llm:
        ordered_ids = [item["id"] for item in reranked]
        rationale_by_id = {item["id"]: item["rationale"] for item in reranked}
    else:
        ordered_ids = [s.book["id"] for s in scored]
        rationale_by_id = {}

    results: List[BookResult] = []
    for book_id in ordered_ids[: req.limit]:
        s = score_by_id[book_id]
        rationale = rationale_by_id.get(book_id) or s.book["why_it_works"]
        results.append(
            BookResult(
                id=s.book["id"],
                title=s.book["title"],
                author=s.book["author"],
                genres=s.book["genres"],
                moods=s.book["moods"],
                matched_genres=s.matched_genres,
                matched_moods=s.matched_moods,
                tag_score=round(s.score, 3),
                rationale=rationale,
                rationale_source="llm" if used_llm else "tag-match",
                cover_url=s.book.get("cover_url"),
                first_publish_year=s.book.get("first_publish_year"),
            )
        )

    return RecommendResponse(
        seed_resolved_title=seed_book["title"] if seed_book else None,
        seed_book=seed_result,
        used_llm_rerank=used_llm,
        results=results,
    )


app.include_router(router)