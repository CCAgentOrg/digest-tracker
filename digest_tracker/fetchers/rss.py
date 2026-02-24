"""RSS feed fetcher."""

import feedparser
from datetime import datetime
from typing import Optional

from .base import BaseFetcher


class RSSFetcher(BaseFetcher):
    """Fetch articles from RSS feeds."""
    
    def fetch(
        self,
        url: str,
        since: Optional[datetime] = None,
        config: Optional[dict] = None
    ) -> list[dict]:
        """Fetch articles from RSS feed."""
        articles = []
        
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                published_at = self._parse_date(entry)
                
                # Filter by date if specified
                if since and published_at:
                    # Make both offset-aware for comparison
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=since.tzinfo) if since.tzinfo else published_at
                    if since.tzinfo is None:
                        since = since.replace(tzinfo=published_at.tzinfo) if published_at.tzinfo else since
                    
                    if published_at < since:
                        continue
                
                article = {
                    "url": entry.get("link", ""),
                    "title": entry.get("title", ""),
                    "content": self._get_content(entry),
                    "published_at": published_at.isoformat() if published_at else None,
                    "author": entry.get("author", ""),
                    "metadata": {
                        "source": feed.feed.get("title", ""),
                        "source_url": url,
                        "tags": [tag.get("term") for tag in entry.get("tags", [])],
                    }
                }
                articles.append(article)
            
        except Exception as e:
            print(f"Error fetching RSS feed {url}: {e}")
        
        return articles
    
    def _parse_date(self, entry) -> Optional[datetime]:
        """Parse published date from RSS entry."""
        import dateutil.parser
        
        for date_field in ["published_parsed", "updated_parsed"]:
            if hasattr(entry, date_field):
                time_struct = getattr(entry, date_field)
                if time_struct:
                    try:
                        return datetime(*time_struct[:6])
                    except Exception:
                        pass
        
        for date_str in ["published", "updated"]:
            if hasattr(entry, date_str):
                try:
                    return dateutil.parser.parse(getattr(entry, date_str))
                except Exception:
                    pass
        
        return None
    
    def _get_content(self, entry) -> str:
        """Extract content from RSS entry."""
        # Try different content fields
        if hasattr(entry, "content") and entry.content:
            if isinstance(entry.content[0], dict):
                return entry.content[0].get("value", "")
            return str(entry.content[0])
        
        if hasattr(entry, "summary"):
            return entry.summary
        
        if hasattr(entry, "description"):
            return entry.description
        
        return ""
    
    def extract_content(self, url: str) -> str:
        """RSS fetcher doesn't extract full content - use web fetcher."""
        from .web import WebFetcher
        return WebFetcher().extract_content(url)
