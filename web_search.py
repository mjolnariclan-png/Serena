import requests
from bs4 import BeautifulSoup
import re
import webbrowser
from pathlib import Path

def search_web(query: str, num_results: int = 3, open_in_browser=True) -> str:
    """
    Search the web and return summarized results.
    Uses DuckDuckGo (no API key needed) for privacy-focused local search.
    Optionally opens the search in Chrome browser.
    """
    try:
        # Construct Google search URL
        search_url = f"https://www.google.com/search?q={query}"
        
        # Open in Chrome if requested
        if open_in_browser:
            try:
                chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
                if Path(chrome_path).exists():
                    webbrowser.get('chrome').open(search_url)
                else:
                    webbrowser.open(search_url)
            except:
                webbrowser.open(search_url)
        
        # Use DuckDuckGo's HTML version for getting results (no API key required)
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
            return f"I've opened the search in Chrome for: '{query}'"
        
        return f"I've opened the search in Chrome for: '{query}'\n\nHere's what I found:\n\n" + "\n\n".join(results)
    
    except requests.RequestException as e:
        return f"Sorry, I couldn't connect to search right now. Error: {str(e)}"
    except Exception as e:
        return f"Something went wrong with the search: {str(e)}"


def is_search_query(text: str) -> bool:
    """
    Determine if a query should trigger web search.
    More comprehensive detection of search intents.
    """
    search_indicators = [
        "search for", "find", "look up", "what is", "who is", 
        "when did", "where is", "how do i", "how to", "define", 
        "latest", "news about", "current", "recent", "recipe",
        "instructions", "tutorial", "guide", "explain", "tell me about",
        "google", "search", "look for", "find out", "information about"
    ]
    
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in search_indicators)


def extract_search_query(text: str) -> str:
    """
    Extract the actual search query from user input.
    Handles natural language patterns like "look up how to make pasta on chrome"
    """
    text_lower = text.lower()
    
    # Remove common search prefixes and suffixes
    prefixes = ["search for", "find", "look up", "what is", "who is", 
                "when did", "where is", "how do i", "how to", "define", 
                "search about", "tell me about", "google", "look for", "find out"]
    
    suffixes = ["on chrome", "in chrome", "using chrome", "on google", "in google", 
                "on the internet", "online", "on the web"]
    
    # Remove prefixes
    for prefix in prefixes:
        if text_lower.startswith(prefix):
            text = text[len(prefix):].strip()
            text_lower = text.lower()
            break
    
    # Remove suffixes
    for suffix in suffixes:
        if text_lower.endswith(suffix):
            text = text[:-len(suffix)].strip()
            text_lower = text.lower()
            break
    
    return text.strip()
