"""
Builds app/catalog_seed.json by fetching each book from Open Library
and tagging it with a local LLM. Run this once to build the catalog,
and again any time you add/remove titles in book_titles.py.

Usage:
    cd backend
    python3 scripts/seed_catalog.py
"""

import json
import re
import time
from pathlib import Path

from book_titles import BOOK_TITLES
from fetch_open_library import fetch_book
from tag_with_llm import tag_book

OUTPUT_PATH = Path(__file__).parent.parent / "app" / "catalog_seed.json"


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def build_catalog() -> tuple[list[dict], list[str]]:
    catalog = []
    failures = []

    for i, (title, author) in enumerate(BOOK_TITLES, start=1):
        print(f"[{i}/{len(BOOK_TITLES)}] {title}...")

        if i > 1:
            time.sleep(0.5)  # light politeness pause

        try:
            book_info = fetch_book(title, author)
        except Exception as e:
            print(f"  ⚠️  Fetch failed: {e}")
            failures.append(title)
            continue

        if not book_info:
            print(f"  ⚠️  Not found, skipping.")
            failures.append(title)
            continue

        try:
            tags = tag_book(
                title=book_info["title"],
                author=", ".join(book_info["authors"]) or author,
                description=book_info["description"] or "",
                categories=book_info["categories"],
            )
        except Exception as e:
            print(f"  ⚠️  Tagging failed: {e}")
            failures.append(title)
            continue

        if not tags:
            print(f"  ⚠️  Tagging failed, skipping.")
            failures.append(title)
            continue

        catalog.append({
            "id": slugify(book_info["title"]),
            "title": book_info["title"],
            "author": ", ".join(book_info["authors"]) or author,
            "genres": tags["genres"],
            "moods": tags["moods"],
            "why_it_works": tags["why_it_works"],
            "cover_url": book_info["thumbnail"],
            "first_publish_year": book_info["published_year"],
            "comp_ids": [],  # filled in by add_comp_ids below
        })
        print(f"  ✓ {tags['genres']} / {tags['moods']}")

    return catalog, failures


def add_comp_ids(catalog: list[dict]) -> list[dict]:
    """
    Simple second pass: for each book, find the 2 other books with the
    most mood-tag overlap and link them as comp_ids. This is what powers
    the small "comp title" boost in similarity scoring.
    """
    for book in catalog:
        overlaps = []
        for other in catalog:
            if other["id"] == book["id"]:
                continue
            shared = len(set(book["moods"]) & set(other["moods"]))
            if shared > 0:
                overlaps.append((shared, other["id"]))
        overlaps.sort(reverse=True)
        book["comp_ids"] = [book_id for _, book_id in overlaps[:2]]
    return catalog


if __name__ == "__main__":
    catalog, failures = build_catalog()
    catalog = add_comp_ids(catalog)

    OUTPUT_PATH.write_text(json.dumps(catalog, indent=2))
    print(f"\nWrote {len(catalog)} books to {OUTPUT_PATH}")
    if failures:
        print(f"Failed: {failures}")