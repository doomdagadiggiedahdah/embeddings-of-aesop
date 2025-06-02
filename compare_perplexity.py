#!/usr/bin/env python3
"""
Compare different t-SNE perplexity values to see clustering differences.
"""

import chromadb
import numpy as np
from sklearn.manifold import TSNE
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Tuple
import time

def extract_embeddings_from_chromadb(db_path: str = "./chroma_db") -> Tuple[np.ndarray, List[dict]]:
    """Extract all embeddings and metadata from ChromaDB."""
    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection("aesop_fables")
    
    print("Extracting embeddings...")
    results = collection.get(include=['embeddings', 'metadatas', 'documents'])
    
    embeddings = np.array(results['embeddings'])
    metadatas = results['metadatas']
    
    print(f"Extracted {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
    
    return embeddings, metadatas

def categorize_fables(metadatas: List[dict]) -> List[str]:
    """Simple categorization of fables based on title keywords."""
    categories = []
    
    for metadata in metadatas:
        title = metadata['title'].lower()
        
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

def compare_perplexity_values(embeddings: np.ndarray, metadatas: List[dict], 
                            perplexity_values: List[int] = [5, 15, 30, 60]):
    """Create t-SNE visualizations with different perplexity values."""
    
    # Prepare metadata
    categories = categorize_fables(metadatas)
    titles = [m['title'] for m in metadatas]
    word_counts = [m['word_count'] for m in metadatas]
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[f'Perplexity = {p}' for p in perplexity_values],
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    # Color mapping for categories
    unique_categories = list(set(categories))
    colors = px.colors.qualitative.Set1[:len(unique_categories)]
    color_map = dict(zip(unique_categories, colors))
    
    for i, perplexity in enumerate(perplexity_values):
        print(f"\n[{i+1}/{len(perplexity_values)}] Running t-SNE with perplexity={perplexity}...")
        start_time = time.time()
        
        # Run t-SNE with verbose output
        tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity, n_iter=1000, verbose=1)
        embeddings_2d = tsne.fit_transform(embeddings)
        
        elapsed_time = time.time() - start_time
        print(f"Completed in {elapsed_time:.1f} seconds")
        
        # Calculate subplot position
        row = (i // 2) + 1
        col = (i % 2) + 1
        
        # Add traces for each category
        for category in unique_categories:
            mask = [c == category for c in categories]
            x_vals = embeddings_2d[mask, 0]
            y_vals = embeddings_2d[mask, 1]
            category_titles = [titles[j] for j, m in enumerate(mask) if m]
            category_word_counts = [word_counts[j] for j, m in enumerate(mask) if m]
            
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode='markers',
                    name=category if i == 0 else None,  # Only show legend for first subplot
                    legendgroup=category,
                    showlegend=(i == 0),
                    marker=dict(
                        color=color_map[category],
                        size=6,
                        opacity=0.7
                    ),
                    text=category_titles,
                    customdata=list(zip(category_titles, category_word_counts)),
                    hovertemplate='<b>%{customdata[0]}</b><br>' +
                                  f'Category: {category}<br>' +
                                  'Word Count: %{customdata[1]}<br>' +
                                  '<extra></extra>'
                ),
                row=row, col=col
            )
    
    # Update layout
    fig.update_layout(
        title_text="t-SNE Visualization: Comparing Different Perplexity Values",
        height=800,
        width=1200,
        showlegend=True
    )
    
    # Update axes labels
    for i in range(1, 5):
        fig.update_xaxes(title_text="t-SNE Dimension 1", row=(i-1)//2+1, col=(i-1)%2+1)
        fig.update_yaxes(title_text="t-SNE Dimension 2", row=(i-1)//2+1, col=(i-1)%2+1)
    
    # Save the plot
    output_file = "fables_tsne_perplexity_comparison.html"
    fig.write_html(output_file)
    print(f"Saved comparison visualization to {output_file}")
    
    return fig

def create_individual_plots(embeddings: np.ndarray, metadatas: List[dict]):
    """Create individual plots for each perplexity value."""
    categories = categorize_fables(metadatas)
    titles = [m['title'] for m in metadatas]
    word_counts = [m['word_count'] for m in metadatas]
    
    perplexity_values = [5, 15, 30, 60]
    
    for i, perplexity in enumerate(perplexity_values):
        print(f"\n[{i+1}/{len(perplexity_values)}] Creating individual plot for perplexity={perplexity}...")
        start_time = time.time()
        
        # Run t-SNE
        tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity, n_iter=1000, verbose=1)
        embeddings_2d = tsne.fit_transform(embeddings)
        
        elapsed_time = time.time() - start_time
        print(f"t-SNE completed in {elapsed_time:.1f} seconds")
        
        # Create DataFrame
        df = pd.DataFrame({
            'x': embeddings_2d[:, 0],
            'y': embeddings_2d[:, 1],
            'title': titles,
            'word_count': word_counts,
            'category': categories
        })
        
        # Create plot
        fig = px.scatter(
            df,
            x='x',
            y='y',
            color='category',
            title=f't-SNE Visualization (Perplexity = {perplexity})',
            labels={'x': 't-SNE Dimension 1', 'y': 't-SNE Dimension 2'},
            hover_data=['title', 'word_count']
        )
        
        fig.update_layout(width=800, height=600)
        
        # Save individual plot
        output_file = f"fables_tsne_perplexity_{perplexity}.html"
        fig.write_html(output_file)
        print(f"Saved to {output_file}")

def main():
    print("Starting t-SNE perplexity comparison...")
    print("This will take several minutes - each t-SNE run takes 1-3 minutes")
    
    # Extract embeddings
    embeddings, metadatas = extract_embeddings_from_chromadb()
    print(f"Processing {len(embeddings)} fables with {embeddings.shape[1]}-dimensional embeddings")
    
    print("\n=== PHASE 1: Creating comparison plot ===")
    start_total = time.time()
    compare_perplexity_values(embeddings, metadatas)
    
    print("\n=== PHASE 2: Creating individual plots ===")
    create_individual_plots(embeddings, metadatas)
    
    total_time = time.time() - start_total
    print(f"\n✅ All done! Total time: {total_time/60:.1f} minutes")
    
    print("\nDone! Open the HTML files to compare:")
    print("- fables_tsne_perplexity_comparison.html (side-by-side view)")
    print("- fables_tsne_perplexity_5.html, _15.html, _30.html, _60.html (individual plots)")
    
    print("\nWhat to look for:")
    print("- Perplexity 5: Very tight, local clusters")
    print("- Perplexity 15: Small distinct groups")
    print("- Perplexity 30: Balanced clustering")  
    print("- Perplexity 60: Broader, global structure")

if __name__ == "__main__":
    main()