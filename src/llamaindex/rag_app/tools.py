import requests
import logging
from .config import settings

logger = logging.getLogger(__name__)


def search_internet(query: str) -> str:
    """
    Search the internet for information using SearXNG.
    Returns a formatted summary of search results.
    """
    try:
        url = f"{settings.SEARXNG_URL}/search"
        params = {
            "q": query,
            "format": "json",
            "engines": "google,duckduckgo,bing"
        }
        logger.info(f"Searching SearXNG: {url} with query: {query}")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            logger.warning("No internet search results found.")
            return "No internet search results found."
            
        summary = []
        for res in results[:5]:  # Take top 5 results
            title = res.get("title", "No Title")
            snippet = res.get("content", "No Description")
            link = res.get("url", "No Link")
            summary.append(f"Title: {title}\nSnippet: {snippet}\nSource: {link}\n")
        
        result_text = "\n".join(summary)
        logger.info(f"Found {len(results)} results, returning top {min(5, len(results))}")
        return result_text
    except Exception as e:
        logger.error(f"Error searching internet: {str(e)}")
        return f"Error searching internet: {str(e)}"
