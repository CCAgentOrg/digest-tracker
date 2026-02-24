"""Local directory publisher (for Jekyll, Hugo, etc.)."""

from pathlib import Path
from typing import Optional
from datetime import datetime

from .base import BasePublisher


class LocalPublisher(BasePublisher):
    """Publish digest posts to local directory."""
    
    def publish(
        self,
        content: str,
        title: str,
        config: dict,
        slug_prefix: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Publish content to local directory."""
        # Get path from config
        path_str = config.get("path")
        if not path_str:
            path_str = config.get("content_dir", config.get("posts_dir", "_posts"))
        
        base_path = Path(path_str).expanduser()
        
        # Check if base_path already includes posts_dir
        posts_dir = config.get("posts_dir", "_posts")
        
        if base_path.name == posts_dir or base_path.suffix == "":
            # Path is the posts directory directly
            posts_path = base_path
        else:
            # Add posts_dir to the path
            posts_path = base_path / posts_dir
        
        # Create directory if needed
        posts_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        date_str = datetime.now().strftime("%Y-%m-%d")
        from ..utils import slugify
        
        # Handle slug prefix with directory
        slug_dir = ""
        slug_file = slugify(title)
        
        if slug_prefix:
            slug_prefix = slug_prefix.rstrip("/")
            if "/" in slug_prefix:
                # Has directory component
                parts = slug_prefix.rsplit("/", 1)
                slug_dir = parts[0]
                slug_prefix_file = parts[1] if len(parts) > 1 else ""
            else:
                slug_prefix_file = slug_prefix
            
            if slug_prefix_file:
                slug_file = f"{slug_prefix_file}-{slug_file}"
        
        filename = f"{date_str}-{slug_file}.md"
        
        # Create full filepath including subdirectories
        if slug_dir:
            posts_path = posts_path / slug_dir
        
        posts_path.mkdir(parents=True, exist_ok=True)
        filepath = posts_path / filename
        
        # Write content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(filepath)
