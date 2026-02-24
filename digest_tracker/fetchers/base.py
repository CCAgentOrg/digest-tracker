"""Base fetcher class."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional


class BaseFetcher(ABC):
    """Base class for content fetchers."""
    
    @abstractmethod
    def fetch(
        self,
        url: str,
        since: Optional[datetime] = None,
        config: Optional[dict] = None
    ) -> list[dict]:
        """
        Fetch articles from a source.
        
        Args:
            url: The source URL
            since: Only fetch articles published after this date
            config: Additional configuration for this fetcher
        
        Returns:
            List of article dicts with keys: url, title, content, published_at, author, metadata
        """
        pass
    
    @abstractmethod
    def extract_content(self, url: str) -> str:
        """Extract full content from a URL."""
        pass
