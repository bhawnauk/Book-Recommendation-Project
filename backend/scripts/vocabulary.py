"""
Fixed tag vocabulary. The LLM tagging step must choose only from these
lists — this is what keeps similarity scoring meaningful across a
catalog seeded by a model rather than hand-curated one at a time.
"""

GENRES = [
    "thriller", "mystery", "cozy-mystery", "dark-comedy", "fantasy", "ya",
    "sci-fi", "horror", "gothic", "romance", "literary-fiction", "memoir",
    "nonfiction",
]

MOODS = [
    "atmospheric", "propulsive", "slow-burn", "cozy", "witty", "dark",
    "twisty", "unreliable-narrator", "melancholy", "hopeful", "epic",
    "immersive", "claustrophobic", "domestic", "lyrical", "cerebral",
    "big-ideas", "found-family", "heist", "whimsical", "uplifting",
    "devastating", "emotional", "glamorous", "banter-heavy",
    "psychological", "clinical", "low-stakes", "high-stakes", "unsettling",
    "coming-of-age", "quiet", "heartwarming", "problem-solving",
]