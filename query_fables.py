#!/usr/bin/env python3
"""
Simple query interface for the Aesop fables ChromaDB collection.
"""

import chromadb
import sys

def query_fables(query: str, n_results: int = 5):
    """Search for fables similar to the query."""
    # Connect to ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("aesop_fables")
    
    # Perform search
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    print(f"Search results for: '{query}'\n")
    
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"{i+1}. {metadata['title']}")
        print(f"   Distance: {distance:.3f} | Word count: {metadata['word_count']}")
        print(f"   Preview: {doc[:150]}...")
        print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python query_fables.py 'your query here'")
        print("Example: python query_fables.py 'fox and grapes'")
        return
    
    query = " ".join(sys.argv[1:])
    query_fables(query)

if __name__ == "__main__":
    main()