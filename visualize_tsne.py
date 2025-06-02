#!/usr/bin/env python3
"""
Create t-SNE visualization of Aesop fables embeddings.
"""

import chromadb
import numpy as np
from sklearn.manifold import TSNE
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import re
from typing import List, Tuple

def extract_embeddings_from_chromadb(db_path: str = "./chroma_db") -> Tuple[np.ndarray, List[dict]]:
    """Extract all embeddings and metadata from ChromaDB."""
    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection("aesop_fables")
    
    print("Extracting embeddings...")
    # Get all documents
    results = collection.get(include=['embeddings', 'metadatas', 'documents'])
    
    embeddings = np.array(results['embeddings'])
    metadatas = results['metadatas']
    documents = results['documents']
    
    print(f"Extracted {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
    
    # Combine metadata with documents for easier handling
    combined_data = []
    for i, (metadata, doc) in enumerate(zip(metadatas, documents)):
        combined_data.append({
            **metadata,
            'document': doc,
            'id': i
        })
    
    return embeddings, combined_data

def categorize_fables(metadatas: List[dict]) -> List[str]:
    """Simple categorization of fables based on title keywords."""
    categories = []
    
    for metadata in metadatas:
        title = metadata['title'].lower()
        
        # Simple keyword-based categorization
        if any(animal in title for animal in ['fox', 'wolf', 'lion', 'bear', 'tiger']):
            category = 'Predators'
        elif any(animal in title for animal in ['hare', 'rabbit', 'mouse', 'deer', 'lamb']):
            category = 'Prey Animals'
        elif any(animal in title for animal in ['dog', 'cat', 'horse', 'ass', 'donkey']):
            category = 'Domestic Animals'
        elif any(bird in title for bird in ['crow', 'eagle', 'owl', 'peacock', 'swan', 'nightingale']):
            category = 'Birds'
        elif any(word in title for word in ['man', 'woman', 'boy', 'girl', 'farmer', 'king', 'merchant']):
            category = 'Human Stories'
        elif any(word in title for word in ['sun', 'wind', 'tree', 'mountain', 'river']):
            category = 'Nature'
        else:
            category = 'Other'
        
        categories.append(category)
    
    return categories

def create_tsne_visualization(embeddings: np.ndarray, metadatas: List[dict], output_file: str = "fables_tsne.html"):
    """Create t-SNE visualization of the embeddings."""
    print("Running t-SNE dimensionality reduction...")
    
    # Run t-SNE
    tsne = TSNE(n_components=2, random_state=42, perplexity=30, n_iter=1000)
    embeddings_2d = tsne.fit_transform(embeddings)
    
    print("Creating visualization...")
    
    # Prepare data for plotting
    categories = categorize_fables(metadatas)
    word_counts = [m['word_count'] for m in metadatas]
    titles = [m['title'] for m in metadatas]
    
    # Create DataFrame
    df = pd.DataFrame({
        'x': embeddings_2d[:, 0],
        'y': embeddings_2d[:, 1],
        'title': titles,
        'word_count': word_counts,
        'category': categories,
        'preview': [m['document'][:100] + '...' if len(m['document']) > 100 else m['document'] 
                   for m in metadatas]
    })
    
    # Create interactive scatter plot
    fig = px.scatter(
        df, 
        x='x', 
        y='y',
        color='category',
        hover_data={
            'title': True,
            'word_count': True,
            'category': True,
            'x': False,
            'y': False
        },
        title='t-SNE Visualization of Aesop Fables (by Category)',
        labels={'x': 't-SNE Dimension 1', 'y': 't-SNE Dimension 2'}
    )
    
    # Customize hover template
    fig.update_traces(
        hovertemplate='<b>%{customdata[0]}</b><br>' +
                      'Category: %{customdata[2]}<br>' +
                      'Word Count: %{customdata[1]}<br>' +
                      '<extra></extra>',
        customdata=df[['title', 'word_count', 'category']].values
    )
    
    # Update layout
    fig.update_layout(
        width=1200,
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    # Save as HTML file
    fig.write_html(output_file)
    print(f"Saved interactive t-SNE visualization to {output_file}")
    
    # Also create a word count version
    fig_wordcount = px.scatter(
        df,
        x='x',
        y='y',
        color='word_count',
        hover_data={
            'title': True,
            'word_count': True,
            'category': True,
            'x': False,
            'y': False
        },
        title='t-SNE Visualization of Aesop Fables (by Word Count)',
        labels={'x': 't-SNE Dimension 1', 'y': 't-SNE Dimension 2'},
        color_continuous_scale='viridis'
    )
    
    fig_wordcount.update_traces(
        hovertemplate='<b>%{customdata[0]}</b><br>' +
                      'Category: %{customdata[2]}<br>' +
                      'Word Count: %{customdata[1]}<br>' +
                      '<extra></extra>',
        customdata=df[['title', 'word_count', 'category']].values
    )
    
    fig_wordcount.update_layout(width=1200, height=800)
    fig_wordcount.write_html(output_file.replace('.html', '_wordcount.html'))
    print(f"Saved word count version to {output_file.replace('.html', '_wordcount.html')}")
    
    return df, fig

def print_cluster_analysis(df: pd.DataFrame):
    """Print some basic analysis of the clusters."""
    print("\n=== Cluster Analysis ===")
    
    # Category distribution
    print("\nCategory Distribution:")
    category_counts = df['category'].value_counts()
    for category, count in category_counts.items():
        print(f"  {category}: {count} fables")
    
    # Word count statistics by category
    print("\nAverage Word Count by Category:")
    for category in df['category'].unique():
        avg_words = df[df['category'] == category]['word_count'].mean()
        print(f"  {category}: {avg_words:.0f} words")
    
    # Find some interesting clusters manually
    print("\nSample of fables by category:")
    for category in df['category'].unique()[:3]:  # Show first 3 categories
        sample_titles = df[df['category'] == category]['title'].head(3).tolist()
        print(f"  {category}: {', '.join(sample_titles)}")

def main():
    # Extract embeddings from ChromaDB
    embeddings, metadatas = extract_embeddings_from_chromadb()
    
    # Create t-SNE visualization
    df, fig = create_tsne_visualization(embeddings, metadatas)
    
    # Print some analysis
    print_cluster_analysis(df)
    
    print(f"\nOpen 'fables_tsne.html' in your browser to view the interactive visualization!")
    print("Each point represents a fable. Similar fables should cluster together.")
    print("Hover over points to see fable details.")

if __name__ == "__main__":
    main()