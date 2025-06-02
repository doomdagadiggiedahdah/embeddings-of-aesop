#!/usr/bin/env python3
"""
Aesop Fables Scraper
Scrapes fables from aesopfables.com and saves them for embedding.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin
from typing import List, Dict, Optional

class AesopScraper:
    def __init__(self, base_url: str = "https://aesopfables.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_search_results(self, last: int = 822) -> List[Dict]:
        """Get search results page and extract fable links."""
        search_url = f"{self.base_url}/cgi/asearch.cgi?terms=a+&boolean=as+a+phrase&case=insensitive&first=1&last={last}"
        
        print(f"Fetching search results for {last} fables...")
        response = self.session.get(search_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links to individual fables
        fables = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and 'aesop1.cgi' in href:
                title = link.get_text().strip()
                if title:
                    # Fix URL construction - the href starts with ./ so we need to resolve relative to /cgi/
                    if href.startswith('./'):
                        full_url = f"{self.base_url}/cgi/{href[2:]}"
                    else:
                        full_url = urljoin(f"{self.base_url}/cgi/", href)
                    fables.append({
                        'title': title,
                        'url': full_url,
                        'relative_path': href
                    })
        
        print(f"Found {len(fables)} fable links")
        return fables
    
    def scrape_fable(self, fable_info: Dict) -> Optional[Dict]:
        """Scrape individual fable content."""
        try:
            print(f"Scraping: {fable_info['title']}")
            response = self.session.get(fable_info['url'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract the main content - usually in the body
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            
            # Try to extract title from the text if it's at the beginning
            title_match = re.search(r'^([A-Z\s]+)\n', text)
            if title_match:
                extracted_title = title_match.group(1).strip()
            else:
                extracted_title = fable_info['title']
            
            return {
                'title': extracted_title,
                'original_title': fable_info['title'],
                'url': fable_info['url'],
                'content': text,
                'word_count': len(text.split())
            }
            
        except Exception as e:
            print(f"Error scraping {fable_info['title']}: {e}")
            return None
    
    def scrape_all_fables(self, max_fables: int = 822, delay: float = 1.0) -> List[Dict]:
        """Scrape all fables with rate limiting."""
        # First get the search results
        fable_links = self.get_search_results(max_fables)
        
        scraped_fables = []
        
        for i, fable_info in enumerate(fable_links, 1):
            print(f"Progress: {i}/{len(fable_links)}")
            
            fable_data = self.scrape_fable(fable_info)
            if fable_data:
                scraped_fables.append(fable_data)
            
            # Rate limiting
            if i < len(fable_links):
                time.sleep(delay)
        
        return scraped_fables
    
    def save_fables(self, fables: List[Dict], filename: str = "aesop_fables.json"):
        """Save scraped fables to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(fables, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(fables)} fables to {filename}")

def main():
    scraper = AesopScraper()
    
    print("Scraping all 822 fables...")
    all_fables = scraper.scrape_all_fables(max_fables=822, delay=0)
    scraper.save_fables(all_fables, "aesop_fables.json")
    
    if all_fables:
        print(f"\nScraping successful! Retrieved {len(all_fables)} fables")
        print(f"Sample fable:")
        print(f"Title: {all_fables[0]['title']}")
        print(f"Word count: {all_fables[0]['word_count']}")
    else:
        print("Scraping failed - no fables retrieved")

if __name__ == "__main__":
    main()
