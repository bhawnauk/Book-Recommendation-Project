"""
Sends a book's description to a local LLM (via Ollama's OpenAI-compatible
endpoint) and asks it to pick mood/genre tags from a fixed vocabulary,
plus write a one-sentence "why it works" note.
"""

import json
import os
from typing import Optional, TypedDict

import httpx
from dotenv import load_dotenv

from vocabulary import GENRES, MOODS

load_dotenv()

LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL")


class TagResult(TypedDict):
    genres: list[str]
    moods: list[str]
    why_it_works: str


SYSTEM_PROMPT = f"""You are a sharp, well-read book editor tagging books for a recommendation system.

Given a book's title, author, description, and Google Books categories, choose:
- 1-2 genres, ONLY from this list: {", ".join(GENRES)}
- 3-6 moods, ONLY from this list: {", ".join(MOODS)}
- a one-sentence "why_it_works" note explaining the SPECIFIC craft reason this book \
works (pacing, structure, voice, tone) — never a generic genre restatement.

CRITICAL: Do not default to generic-sounding tags like "atmospheric", "twisty", or \
"slow-burn" out of habit. Pick the moods that most SPECIFICALLY and ACCURATELY \
describe THIS book, even if that means using less common tags like "heist", \
"big-ideas", "problem-solving", "found-family", "banter-heavy", "cerebral", or \
"coming-of-age". Two different books should rarely get identical mood sets unless \
they are genuinely very similar in tone and structure.

Examples of good, specific tagging:

Book: "The Martian" — an astronaut stranded on Mars engineers his way to survival \
using science and dry humor.
Good moods: ["propulsive", "hopeful", "problem-solving", "witty"]
Bad moods: ["atmospheric", "twisty", "slow-burn"] — generic, ignores that this book \
is fundamentally about competence and problem-solving, not mystery or tone.

Book: "Six of Crows" — a crew of teenage criminals pull off an impossible heist \
with fast-rotating POV chapters and a ticking clock.
Good moods: ["heist", "propulsive", "witty", "found-family"]
Bad moods: ["atmospheric", "melancholy"] — misses that the core appeal is heist \
mechanics and ensemble banter, not mood or tone.

Every field, including why_it_works, MUST be wrapped in double quotes. Double-check \
the JSON is syntactically valid before answering.

Respond with ONLY valid JSON, no markdown fences, no preamble:
{{"genres": [...], "moods": [...], "why_it_works": "..."}}
"""


def tag_book(
    title: str, author: str, description: str, categories: list[str], attempts: int = 3
) -> Optional[TagResult]:
    if not LOCAL_LLM_MODEL:
        raise RuntimeError("LOCAL_LLM_MODEL not set in .env")

    user_prompt = (
        f"Title: {title}\nAuthor: {author}\n"
        f"Google Books categories: {', '.join(categories) or 'none'}\n"
        f"Description: {description or 'none available'}"
    )

    payload = {
        "model": LOCAL_LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "stream": False,
    }

    for attempt in range(attempts):
        resp = httpx.post(f"{LOCAL_LLM_BASE_URL}/chat/completions", json=payload, timeout=90.0)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            if attempt < attempts - 1:
                print(f"  ⚠️  Malformed JSON for '{title}', retrying ({attempt + 1}/{attempts})...")
                continue
            print(f"  ⚠️  Gave up on '{title}' after {attempts} attempts. Raw output:\n{raw}")
            return None

        genres = [g for g in parsed.get("genres", []) if g in GENRES]
        moods = [m for m in parsed.get("moods", []) if m in MOODS]
        why = parsed.get("why_it_works", "").strip()

        if not genres or not moods or not why:
            if attempt < attempts - 1:
                print(f"  ⚠️  Incomplete tags for '{title}', retrying ({attempt + 1}/{attempts})...")
                continue
            print(
                f"  ⚠️  Incomplete tags for '{title}' after {attempts} attempts: "
                f"genres={genres}, moods={moods}"
            )
            return None

        return {"genres": genres, "moods": moods, "why_it_works": why}

    return None


if __name__ == "__main__":
    result = tag_book(
        title="Gone Girl",
        author="Gillian Flynn",
        description=(
            "On a warm summer morning in North Carthage, Missouri, it is Nick "
            "and Amy Dunne's fifth wedding anniversary. Presents are being "
            "wrapped and reservations are being made when Nick's clever and "
            "beautiful wife disappears."
        ),
        categories=["Fiction"],
    )
    print(json.dumps(result, indent=2))