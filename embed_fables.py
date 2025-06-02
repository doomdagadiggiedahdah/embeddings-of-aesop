#!/usr/bin/env python3
"""
Aesop Fables Embedding Script
Loads scraped fables and creates embeddings using ChromaDB.
"""

import json
import chromadb
from chromadb.config import Settings
import re
from typing import List, Dict
import os

class FableEmbedder:
    def __init__(self, data_file: str = "aesop_fables.json", db_path: str = "./chroma_db"):
        self.data_file = data_file
        self.db_path = db_path
        self.client = None
        self.collection = None
        
    def load_fables(self) -> List[Dict]:
        """Load fables from JSON file."""
        print(f"Loading fables from {self.data_file}...")
        with open(self.data_file, 'r', encoding='utf-8') as f:
            fables = json.load(f)
        print(f"Loaded {len(fables)} fables")
        return fables
    
    def clean_content(self, content: str) -> str:
        """Clean fable content for embedding."""
        # Remove website header
        content = re.sub(r'^AesopFables\.com.*?\n', '', content)
        
        # Remove footer/copyright
        content = re.sub(r'Process took:.*?Copyright.*?$', '', content, flags=re.DOTALL)
        content = re.sub(r'RETURN\s*Process took.*?$', '', content, flags=re.DOTALL)
        content = re.sub(r'THE END\s*RETURN.*?$', '', content, flags=re.DOTALL)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = content.strip()
        
        return content
    
    def setup_chromadb(self):
        """Initialize ChromaDB client and collection."""
        print(f"Setting up ChromaDB at {self.db_path}...")
        
        # Create directory if it doesn't exist
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection("aesop_fables")
            print("Found existing collection 'aesop_fables'")
        except:
            self.collection = self.client.create_collection(
                name="aesop_fables",
                metadata={"description": "Aesop fables and stories collection"}
            )
            print("Created new collection 'aesop_fables'")
    
    def embed_fables(self, fables: List[Dict]):
        """Add fables to ChromaDB with embeddings."""
        print(f"Adding {len(fables)} fables to ChromaDB...")
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for i, fable in enumerate(fables):
            # Clean content
            cleaned_content = self.clean_content(fable['content'])
            
            # Create document
            documents.append(cleaned_content)
            
            # Create metadata
            metadatas.append({
                "title": fable['title'],
                "original_title": fable['original_title'],
                "url": fable['url'],
                "word_count": fable['word_count'],
                "cleaned_length": len(cleaned_content)
            })
            
            # Create ID
            ids.append(f"fable_{i:04d}")
        
        # Add to collection in batches (ChromaDB has batch size limits)
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            batch_docs = documents[i:end_idx]
            batch_meta = metadatas[i:end_idx]
            batch_ids = ids[i:end_idx]
            
            print(f"Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_meta,
                ids=batch_ids
            )
        
        print("All fables embedded successfully!")
    
    def test_search(self, query: str = "fox and grapes", n_results: int = 3):
        """Test the embedding by searching for similar fables."""
        print(f"\nTesting search with query: '{query}'")
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        print(f"Found {len(results['documents'][0])} results:")
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0], 
            results['distances'][0]
        )):
            print(f"\n{i+1}. {metadata['title']} (distance: {distance:.3f})")
            print(f"   Word count: {metadata['word_count']}")
            print(f"   Preview: {doc[:200]}...")
    
    def get_collection_info(self):
        """Print information about the collection."""
        if self.collection:
            count = self.collection.count()
            print(f"\nCollection 'aesop_fables' contains {count} documents")
            return count
        return 0

def main():
    embedder = FableEmbedder()
    
    # Load fables
    fables = embedder.load_fables()
    
    # Setup ChromaDB
    embedder.setup_chromadb()
    
    # Check if collection already has data
    existing_count = embedder.get_collection_info()
    
    if existing_count > 0:
        print(f"Collection already contains {existing_count} documents.")
        proceed = input("Do you want to recreate the collection? (y/n): ").lower().strip()
        if proceed == 'y':
            # Delete and recreate collection
            embedder.client.delete_collection("aesop_fables")
            embedder.collection = embedder.client.create_collection(
                name="aesop_fables",
                metadata={"description": "Aesop fables and stories collection"}
            )
            print("Recreated collection")
        else:
            print("Using existing collection")
    
    # Only embed if collection is empty or was recreated
    if existing_count == 0 or (existing_count > 0 and input("Do you want to recreate the collection? (y/n): ").lower().strip() == 'y'):
        embedder.embed_fables(fables)
    
    # Test the embeddings
    embedder.test_search("fox and grapes")
    embedder.test_search("tortoise and hare")
    embedder.test_search("lion and mouse")
    
    # Final collection info
    embedder.get_collection_info()

if __name__ == "__main__":
    main()