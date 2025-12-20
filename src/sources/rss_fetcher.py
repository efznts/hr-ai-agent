
"""
RSS feed fetcher for HR news sources.
"""
import feedparser
from datetime import datetime
from typing import List
from config.settings import RSS_SOURCES


class RSSFetcher:
    """Fetches and parses RSS feeds from HR news sources."""
    
    def __init__(self):
        self.sources = RSS_SOURCES
    
    def fetch_all(self) -> List[dict]:
        """Fetch from all configured RSS sources."""
        all_items = []
        for source in self.sources:
            items = self._fetch_source(source)
            all_items.extend(items)
        return all_items
    
    def _fetch_source(self, source: dict) -> List[dict]:
        """Fetch items from a single RSS source."""
        items = []
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:10]:  # Limit to 10 per source
                item = {
                    "id": entry.get("id", entry.get("link", "")),
                    "url": entry.get("link", ""),
                    "title": entry.get("title", ""),
                    "content": entry.get("summary", entry.get("description", "")),
                    "published": entry.get("published", ""),
                    "source": source["name"],
                    "lang": source.get("lang", "en"),
                    "type": "rss"
                }
                items.append(item)
        except Exception as e:
            print(f"Error fetching {source['name']}: {e}")
        return items

