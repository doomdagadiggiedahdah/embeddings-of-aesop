#!/usr/bin/env python3
"""
Deduplicate fables by title and keep the best version of each story.
"""

import json
import re
from typing import List, Dict
from collections import defaultdict

def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    # Convert to lowercase
    title = title.lower()
    
    # Remove common prefixes/suffixes
    title = re.sub(r'^(the|a|an)\s+', '', title)
    title = re.sub(r'\s+(fable|story|tale)$', '', title)
    
    # Remove punctuation and extra spaces
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title

def choose_best_version(duplicates: List[Dict]) -> Dict:
    """Choose the best version from duplicates based on word count and content quality."""
    # Prefer versions with moderate word count (not too short, not extremely long)
    scored_versions = []
    
    for fable in duplicates:
        word_count = fable['word_count']
        content = fable['content']
        
        # Score based on word count (prefer 100-500 words)
        if 100 <= word_count <= 500:
            word_score = 1.0
        elif 50 <= word_count < 100:
            word_score = 0.8
        elif 500 < word_count <= 1000:
            word_score = 0.9
        else:
            word_score = 0.5
        
        # Score based on content quality (prefer versions without too much metadata)
        content_score = 1.0
        if 'AesopFables.com' in content:
            content_score -= 0.1
        if 'Process took:' in content:
            content_score -= 0.2
        if 'Copyright' in content:
            content_score -= 0.1
        
        # Prefer versions with moral/lesson at the end
        if any(word in content.lower() for word in ['moral:', 'lesson:', 'application:']):
            content_score += 0.2
        
        total_score = word_score * content_score
        scored_versions.append((total_score, fable))
    
    # Return the highest scored version
    return max(scored_versions, key=lambda x: x[0])[1]

def deduplicate_fables(input_file: str = "aesop_fables.json", output_file: str = "aesop_fables_deduplicated.json"):
    """Remove duplicate fables based on title similarity."""
    print(f"Loading fables from {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        fables = json.load(f)
    
    print(f"Original count: {len(fables)} fables")
    
    # Group fables by normalized title
    title_groups = defaultdict(list)
    
    for fable in fables:
        normalized_title = normalize_title(fable['title'])
        title_groups[normalized_title].append(fable)
    
    # Keep only the best version of each title
    deduplicated_fables = []
    duplicates_found = 0
    removed_stories = []
    
    for normalized_title, group in title_groups.items():
        if len(group) > 1:
            duplicates_found += len(group) - 1
            print(f"Found {len(group)} versions of: '{normalized_title}'")
            
            # Show the different versions
            for i, fable in enumerate(group, 1):
                print(f"  {i}. {fable['title']} ({fable['word_count']} words)")
            
            # Choose the best version
            best_version = choose_best_version(group)
            print(f"  → Keeping: {best_version['title']} ({best_version['word_count']} words)")
            print()
            
            # Track removed stories
            for fable in group:
                if fable != best_version:
                    # Extract suffix from URL like /hca/a126
                    url_suffix = fable['url'].split('?srch&')[-1] if '?srch&' in fable['url'] else fable['url']
                    removed_stories.append(url_suffix)
            
            deduplicated_fables.append(best_version)
        else:
            deduplicated_fables.append(group[0])
    
    print(f"Removed {duplicates_found} duplicates")
    print(f"Final count: {len(deduplicated_fables)} unique fables")
    
    # Save deduplicated fables
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_fables, f, indent=2, ensure_ascii=False)
    
    print(f"Saved deduplicated fables to {output_file}")
    
    # Save list of removed stories
    with open("removed_stories.txt", 'w', encoding='utf-8') as f:
        f.write("Removed Story URL Suffixes (Duplicates):\n\n")
        for suffix in removed_stories:
            f.write(f"{suffix}\n")
    
    print(f"Saved list of {len(removed_stories)} removed stories to removed_stories.txt")
    
    return deduplicated_fables

def main():
    deduplicated_fables = deduplicate_fables()
    
    # Show some statistics
    word_counts = [f['word_count'] for f in deduplicated_fables]
    print(f"\nStatistics after deduplication:")
    print(f"  Total fables: {len(deduplicated_fables)}")
    print(f"  Word count range: {min(word_counts)} - {max(word_counts)}")
    print(f"  Average word count: {sum(word_counts) // len(word_counts)}")

if __name__ == "__main__":
    main()