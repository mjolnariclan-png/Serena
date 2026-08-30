import requests
from bs4 import BeautifulSoup
import re

def search_web(query: str, num_results: int = 3) -> str:
    """
    Search the web and return summarized results.
    Uses DuckDuckGo (no API key needed) for privacy-focused local search.
    """
    try:
        # Use DuckDuckGo's HTML version (no API key required)
        url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find search result snippets
        results = []
        result_divs = soup.find_all('div', class_='result')
        
        for div in result_divs[:num_results]:
            try:
                title_tag = div.find('a', class_='result__a')
                snippet_tag = div.find('a', class_='result__snippet')
                
                if title_tag and snippet_tag:
                    title = title_tag.get_text(strip=True)
                    snippet = snippet_tag.get_text(strip=True)
                    results.append(f"• {title}\n  {snippet}")
            except Exception:
                continue
        
        if not results:
            return "I couldn't find any results for that search."
        
        return f"Here's what I found about '{query}':\n\n" + "\n\n".join(results)
    
    except requests.RequestException as e:
        return f"Sorry, I couldn't connect to search right now. Error: {str(e)}"
    except Exception as e:
        return f"Something went wrong with the search: {str(e)}"


def is_search_query(text: str) -> bool:
    """
    Determine if a query should trigger web search.
    """
    search_indicators = [
        "search for", "find", "look up", "what is", "who is", 
        "when did", "where is", "how do i", "define", 
        "latest", "news about", "current", "recent"
    ]
    
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in search_indicators)


def extract_search_query(text: str) -> str:
    """
    Extract the actual search query from user input.
    """
    # Remove common search prefixes
    prefixes = ["search for", "find", "look up", "what is", "who is", 
                "when did", "where is", "how do i", "define", 
                "search about", "tell me about"]
    
    text_lower = text.lower()
    for prefix in prefixes:
        if text_lower.startswith(prefix):
            return text[len(prefix):].strip()
    
    return text.strip()
