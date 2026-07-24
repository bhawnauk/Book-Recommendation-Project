"""
Tag-based similarity scoring.

Books are encoded as weighted tag sets (genre + mood) and scored
against a seed (either another book, or a free-form genre/mood query)
using a weighted Jaccard-style overlap. Mood tags are weighted higher
than genre tags, since "what made the book work" tends to live in
tone/pacing/structure more than shelf category. A direct comp-title
relationship (from catalog_seed.json's comp_ids) gives an additional
boost.
"""

from dataclasses import dataclass
from typing import List, Optional, Set

from .data import Book, BOOKS, get_book

GENRE_WEIGHT = 1.0
MOOD_WEIGHT = 1.6
COMP_TITLE_BOOST = 1.5


@dataclass
class ScoredBook:
    book: Book
    score: float
    matched_genres: List[str]
    matched_moods: List[str]


def _weighted_overlap(
    a_genres: Set[str], a_moods: Set[str], b_genres: Set[str], b_moods: Set[str]
):
    genre_overlap = a_genres & b_genres
    mood_overlap = a_moods & b_moods

    genre_union = a_genres | b_genres
    mood_union = a_moods | b_moods

    genre_score = (len(genre_overlap) / len(genre_union)) if genre_union else 0.0
    mood_score = (len(mood_overlap) / len(mood_union)) if mood_union else 0.0

    total = (genre_score * GENRE_WEIGHT) + (mood_score * MOOD_WEIGHT)
    return total, sorted(genre_overlap), sorted(mood_overlap)


def score_against_book(seed: Book, candidate: Book) -> ScoredBook:
    score, g_match, m_match = _weighted_overlap(
        set(seed["genres"]), set(seed["moods"]),
        set(candidate["genres"]), set(candidate["moods"]),
    )
    if candidate["id"] in seed.get("comp_ids", []):
        score *= COMP_TITLE_BOOST
    return ScoredBook(book=candidate, score=score, matched_genres=g_match, matched_moods=m_match)


def score_against_query(genres: Set[str], moods: Set[str], candidate: Book) -> ScoredBook:
    score, g_match, m_match = _weighted_overlap(
        genres, moods, set(candidate["genres"]), set(candidate["moods"]),
    )
    return ScoredBook(book=candidate, score=score, matched_genres=g_match, matched_moods=m_match)


def recommend_from_book(seed_book_id: str, limit: int = 6) -> List[ScoredBook]:
    seed = get_book(seed_book_id)
    if not seed:
        return []
    scored = [score_against_book(seed, b) for b in BOOKS if b["id"] != seed_book_id]
    scored.sort(key=lambda s: s.score, reverse=True)
    return [s for s in scored if s.score > 0][:limit]


def recommend_from_tags(
    genres: Optional[List[str]], moods: Optional[List[str]], limit: int = 6
) -> List[ScoredBook]:
    g = {x.strip().lower() for x in (genres or []) if x.strip()}
    m = {x.strip().lower() for x in (moods or []) if x.strip()}
    scored = [score_against_query(g, m, b) for b in BOOKS]
    scored.sort(key=lambda s: s.score, reverse=True)
    return [s for s in scored if s.score > 0][:limit]