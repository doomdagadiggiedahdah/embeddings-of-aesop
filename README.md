# Aesop Fables Embedding Project

This project scrapes 822 fables from aesopfables.com and creates semantic embeddings using ChromaDB.

## How to Use

Install dependencies: `uv install`

Scrape fables: `uv run python scrape_fables.py`

Remove duplicates: `uv run python deduplicate_fables.py`

Create embeddings: `uv run python embed_fables.py`

Search fables: `uv run python query_fables.py "your search query"`

Example: `uv run python query_fables.py "fox and grapes"`

## Deduplication

Removed 63 duplicates (822 → 759 unique fables). Found multiple versions of classics like "Hare and Tortoise" (4 versions), "Lion and Mouse" (4 versions). See `removed_stories.txt` for complete list of removed URL suffixes.