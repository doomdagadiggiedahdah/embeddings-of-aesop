# Aesop Fables Embedding Project

This project scrapes 822 fables from aesopfables.com and creates semantic embeddings using ChromaDB.

## How to Use

Install dependencies: `uv install`

Scrape fables: `uv run python scrape_fables.py`

Create embeddings: `uv run python embed_fables.py`

Search fables: `uv run python query_fables.py "your search query"`

Example: `uv run python query_fables.py "fox and grapes"`