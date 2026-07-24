"""
One-time QA correction pass over the LLM-generated catalog. Local-model
tagging got us ~85% of the way there automatically; this fixes the
specific issues a manual review caught: overused default tags, a
misclassified genre, inconsistent title casing, one mis-fetched book,
and two books that failed to seed entirely.

Run this once, after seed_catalog.py, whenever you regenerate the seed.
"""

import json
import re
from pathlib import Path

CATALOG_PATH = Path(__file__).parent.parent / "app" / "catalog_seed.json"

# Field overrides, matched by a case-insensitive substring of the
# auto-generated title. Only lists fields that need to change — genres,
# moods, or title casing fixes.
CORRECTIONS = {
    "silent patient": {
        "moods": ["twisty", "unreliable-narrator", "clinical", "psychological"],
    },
    "sharp objects": {
        "genres": ["thriller", "literary-fiction"],
    },
    "my sister": {
        "title": "My Sister, the Serial Killer",
        "genres": ["thriller", "dark-comedy"],
    },
    "project hail mary": {
        "moods": ["propulsive", "hopeful", "problem-solving", "witty"],
    },
    "children of time": {
        "moods": ["epic", "big-ideas", "propulsive", "hopeful"],
    },
    "name of the wind": {
        "moods": ["epic", "immersive", "lyrical", "slow-burn"],
    },
    "darker shade of magic": {
        "moods": ["epic", "immersive", "twisty", "propulsive"],
    },
    "piranesi": {
        "moods": ["claustrophobic", "lyrical", "unreliable-narrator", "melancholy"],
    },
    "never let me go": {
        "genres": ["literary-fiction", "sci-fi"],
        "moods": ["melancholy", "quiet", "slow-burn", "devastating"],
    },
    "cerulean sea": {
        "title": "The House in the Cerulean Sea",
        "genres": ["fantasy", "romance"],
    },
    "seven husbands": {
        "genres": ["romance", "literary-fiction"],
        "moods": ["emotional", "twisty", "unreliable-narrator", "glamorous"],
    },
    "daisy jones": {
        "genres": ["romance", "literary-fiction"],
        "moods": ["twisty", "unreliable-narrator", "emotional", "glamorous"],
    },
    "mexican gothic": {
        "genres": ["horror", "gothic"],
    },
    "haunting of hill house": {
        "genres": ["horror", "gothic"],
    },
    "rebecca": {
        "genres": ["gothic", "mystery"],
    },
    "educated": {
        "moods": ["devastating", "hopeful", "emotional", "uplifting"],
    },
    "glass castle": {
        "moods": ["devastating", "melancholy", "domestic", "emotional"],
    },
    "born a crime": {
        "moods": ["witty", "propulsive", "hopeful", "emotional"],
    },
    "thursday murder club": {
        "genres": ["mystery", "cozy-mystery"],
        "moods": ["cozy", "witty", "found-family", "hopeful"],
    },
    "circe": {
        "moods": ["epic", "lyrical", "slow-burn", "emotional"],
    },
}

# The Google/Open Library fetch matched the wrong book in the trilogy —
# full replacement rather than a partial correction.
THREE_BODY_REPLACEMENT = {
    "id": "the-three-body-problem",
    "title": "The Three-Body Problem",
    "author": "Liu Cixin",
    "genres": ["sci-fi"],
    "moods": ["big-ideas", "cerebral", "slow-burn", "unsettling"],
    "why_it_works": (
        "Hard-science speculation used to generate genuine dread about first "
        "contact — the ideas themselves are the plot engine."
    ),
    "cover_url": None,
    "first_publish_year": 2008,
    "comp_ids": [],
}

# Books that failed during seeding — added by hand instead of rerunning
# the whole batch.
MISSING_BOOKS = [
    {
        "id": "klara-and-the-sun",
        "title": "Klara and the Sun",
        "author": "Kazuo Ishiguro",
        "genres": ["literary-fiction", "sci-fi"],
        "moods": ["melancholy", "lyrical", "slow-burn", "quiet", "unsettling"],
        "why_it_works": (
            "A narrator with limited understanding lets the reader feel the "
            "emotional weight before the character does — restraint "
            "generates the ache."
        ),
        "cover_url": None,
        "first_publish_year": 2021,
        "comp_ids": [],
    },
    {
        "id": "a-man-called-ove",
        "title": "A Man Called Ove",
        "author": "Fredrik Backman",
        "genres": ["literary-fiction"],
        "moods": ["cozy", "witty", "uplifting", "found-family", "heartwarming"],
        "why_it_works": (
            "A grump slowly thawed by an accidental community — humor and "
            "warmth are earned through specific, small acts, not "
            "sentimentality."
        ),
        "cover_url": None,
        "first_publish_year": 2012,
        "comp_ids": [],
    },
]


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def add_comp_ids(catalog: list[dict]) -> list[dict]:
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


def main():
    catalog = json.loads(CATALOG_PATH.read_text())

    corrected_count = 0
    replaced_count = 0
    kept = []

    for book in catalog:
        title_lower = book["title"].lower()

        if "dark forest" in title_lower:
            kept.append(THREE_BODY_REPLACEMENT)
            replaced_count += 1
            print(f"  ↳ Replaced mis-fetched '{book['title']}' with correct Three-Body Problem entry")
            continue

        matched_key = next((k for k in CORRECTIONS if k in title_lower), None)
        if matched_key:
            fix = CORRECTIONS[matched_key]
            if "title" in fix:
                book["title"] = fix["title"]
                book["id"] = slugify(fix["title"])
            if "genres" in fix:
                book["genres"] = fix["genres"]
            if "moods" in fix:
                book["moods"] = fix["moods"]
            corrected_count += 1
            print(f"  ✓ Corrected: {book['title']}")

        kept.append(book)

    existing_ids = {b["id"] for b in kept}
    added_count = 0
    for missing in MISSING_BOOKS:
        if missing["id"] not in existing_ids:
            kept.append(missing)
            added_count += 1
            print(f"  + Added missing: {missing['title']}")

    kept = add_comp_ids(kept)

    CATALOG_PATH.write_text(json.dumps(kept, indent=2))
    print(
        f"\nDone. {corrected_count} corrected, {replaced_count} replaced, "
        f"{added_count} added. {len(kept)} total books in catalog."
    )


if __name__ == "__main__":
    main()