"""Content fetchers for different source types."""

from .base import BaseFetcher
from .rss import RSSFetcher
from .web import WebFetcher

__all__ = ["BaseFetcher", "RSSFetcher", "WebFetcher"]

def get_fetcher(source_type: str) -> "BaseFetcher":
    """Get fetcher instance for source type."""
    fetchers = {
        "rss": RSSFetcher(),
        "web": WebFetcher(),
    }
    if source_type not in fetchers:
        raise ValueError(f"Unknown source type: {source_type}")
    return fetchers[source_type]
