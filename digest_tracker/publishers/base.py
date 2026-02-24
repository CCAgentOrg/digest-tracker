"""Base publisher class."""

from abc import ABC, abstractmethod
from typing import Optional


class BasePublisher(ABC):
    """Base class for blog publishers."""
    
    @abstractmethod
    def publish(
        self,
        content: str,
        title: str,
        config: dict,
        slug_prefix: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Publish content to blog.
        
        Args:
            content: The content to publish
            title: Post title
            config: Blog configuration
            slug_prefix: URL slug prefix
            metadata: Additional metadata (tags, categories, etc.)
        
        Returns:
            Published URL
        """
        pass
