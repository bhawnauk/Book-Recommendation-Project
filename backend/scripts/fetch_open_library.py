"""
Sole book metadata source. Open Library needs no API key and has no
meaningful rate limit at this volume.

Two-step fetch: search.json gives us a match + work key, then the work
detail endpoint often has a real description (search results usually
don't) — worth the extra request for better material to hand the LLM
tagging step.
"""

from typing import Optional

import httpx

SEARCH_URL = "https://openlibrary.org/search.json"
WORK_URL_TEMPLATE = "https://openlibrary.org{work_key}.json"
COVER_URL_TEMPLATE = "https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"

HEADERS = {"User-Agent": "book-recommender/0.1 (portfolio project)"}


def _fetch_description(work_key: str) -> Optional[str]:
    try:
        resp = httpx.get(WORK_URL_TEMPLATE.format(work_key=work_key), timeout=10.0, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError:
        return None

    desc = data.get("description")
    if isinstance(desc, dict):
        return desc.get("value")
    if isinstance(desc, str):
        return desc
    return None


def fetch_book(title: str, author: Optional[str] = None) -> Optional[dict]:
    params = {"title": title, "limit": 1}
    if author:
        params["author"] = author

    resp = httpx.get(SEARCH_URL, params=params, timeout=10.0, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    docs = data.get("docs") or []
    if not docs:
        return None

    doc = docs[0]
    cover_id = doc.get("cover_i")
    subjects = doc.get("subject", [])[:6]
    work_key = doc.get("key")  # e.g. "/works/OL27479W"

    description = _fetch_description(work_key) if work_key else None

    return {
        "title": doc.get("title", title),
        "authors": doc.get("author_name", [author] if author else []),
        "description": description,
        "categories": subjects,
        "thumbnail": COVER_URL_TEMPLATE.format(cover_id=cover_id) if cover_id else None,
        "published_year": doc.get("first_publish_year"),
        "google_books_id": None,
    }


if __name__ == "__main__":
    import json
    result = fetch_book("Gone Girl", "Gillian Flynn")
    print(json.dumps(result, indent=2))