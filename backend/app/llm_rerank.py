"""
Optional LLM re-ranking pass for live recommendation requests. Tag
similarity (similarity.py) gets a fast, deterministic shortlist; this
hands that shortlist to a local LLM to reorder by genuine fit and
write a specific one-sentence rationale per book.

If LOCAL_LLM_MODEL isn't set, rerank() returns None and main.py falls
back to tag-only ordering with the catalog's stored why_it_works text.
"""

import json
import os
from typing import List, Optional, TypedDict

import httpx

from .data import Book
from .similarity import ScoredBook

LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL")


class RerankedItem(TypedDict):
    id: str
    rationale: str


SYSTEM_PROMPT = (
    "You are a sharp, well-read book recommender. You explain WHY a book "
    "fits a request in concrete craft terms (pacing, structure, voice, "
    "tone) — never generic genre restatements like 'it's also a "
    "thriller'. Respond with ONLY valid JSON, no markdown fences, no "
    "preamble: a JSON array of objects with keys 'id' and 'rationale'. "
    "Order the array by genuine fit, best first. 'rationale' must be "
    "one sentence, specific, under 30 words."
)


def _seed_description(seed_book: Optional[Book], genres: List[str], moods: List[str]) -> str:
    if seed_book:
        return (
            f'the book "{seed_book["title"]}" by {seed_book["author"]}, which works '
            f'because: {seed_book["why_it_works"]}'
        )
    parts = []
    if genres:
        parts.append(f"genre(s): {', '.join(genres)}")
    if moods:
        parts.append(f"mood(s): {', '.join(moods)}")
    return "a request for " + (" and ".join(parts) if parts else "a general recommendation")


async def rerank(
    scored: List[ScoredBook],
    seed_book: Optional[Book],
    genres: List[str],
    moods: List[str],
) -> Optional[List[RerankedItem]]:
    if not LOCAL_LLM_MODEL or not scored:
        return None

    candidates = [
        {
            "id": s.book["id"],
            "title": s.book["title"],
            "author": s.book["author"],
            "genres": s.book["genres"],
            "moods": s.book["moods"],
            "why_it_works": s.book["why_it_works"],
            "tag_score": round(s.score, 3),
        }
        for s in scored
    ]

    user_prompt = (
        f"The reader is looking for something like {_seed_description(seed_book, genres, moods)}.\n\n"
        f"Here are tag-similarity-matched candidates as JSON:\n"
        f"{json.dumps(candidates, indent=2)}\n\n"
        "Re-rank these by genuine fit and write one specific rationale sentence each. "
        "Return ALL of the candidates, just reordered with rationale."
    )

    payload = {
        "model": LOCAL_LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "stream": False,
    }

    try:
        timeout = httpx.Timeout(connect=5.0, read=45.0, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{LOCAL_LLM_BASE_URL}/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
        raw = data["choices"][0]["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return None

    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(raw)
        valid_ids = {c["id"] for c in candidates}
        result = [
            {"id": item["id"], "rationale": item["rationale"]}
            for item in parsed
            if isinstance(item, dict) and item.get("id") in valid_ids
        ]
        return result or None
    except (json.JSONDecodeError, KeyError, TypeError):
        return None