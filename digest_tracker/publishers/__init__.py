"""Blog publishers for different blog types."""

from .base import BasePublisher
from .local import LocalPublisher

__all__ = ["BasePublisher", "LocalPublisher"]

def get_publisher(blog_type: str) -> "BasePublisher":
    """Get publisher instance for blog type."""
    publishers = {
        "local": LocalPublisher(),
    }
    if blog_type not in publishers:
        raise ValueError(f"Unknown blog type: {blog_type}")
    return publishers[blog_type]
