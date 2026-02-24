"""Local directory publisher (for Jekyll, Hugo, etc.)."""

from pathlib import Path
from typing import Optional
from datetime import datetime
import time

from .base import BasePublisher


class LocalPublisher(BasePublisher):
    """Publish digest posts to local directory."""
    
    def __init__(self):
        self._timestamp_counter = 0
    
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
        
        # If the path explicitly ends with the posts_dir name, treat it as the posts directory
        if base_path.name == posts_dir:
            # Path is the posts directory directly
            posts_path = base_path
        else:
            # Add posts_dir to the path (blog root + posts_dir)
            posts_path = base_path / posts_dir
        
        # Create directory if needed
        posts_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp for uniqueness
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_suffix = datetime.now().strftime("%H%M%S")
        
        # Add counter for uniqueness
        self._timestamp_counter += 1
        unique_suffix = f"{time_suffix}-{self._timestamp_counter}"
        
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
        
        filename = f"{date_str}-{unique_suffix}-{slug_file}.md"
        
        # Create full filepath including subdirectories
        final_path = posts_path
        if slug_dir:
            final_path = final_path / slug_dir
        
        final_path.mkdir(parents=True, exist_ok=True)
        filepath = final_path / filename
        
        # Prepare content with frontmatter if enabled
        final_content = content
        
        if config.get("frontmatter", False):
            frontmatter = self._generate_frontmatter(
                title,
                config,
                metadata or {}
            )
            final_content = f"{frontmatter}\n\n{content}"
        
        # Write content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_content)
        
        return str(filepath)
    
    def _generate_frontmatter(self, title: str, config: dict, metadata: dict) -> str:
        """Generate frontmatter in the requested format."""
        frontmatter_format = config.get("frontmatter_format", "yaml")
        frontmatter_fields = config.get("frontmatter_fields", {})
        
        # Build frontmatter dictionary
        fm = {
            "title": title,
            "date": datetime.now().isoformat(),
            **frontmatter_fields,
            **metadata
        }
        
        # Add layout if specified
        if "layout" in config:
            fm["layout"] = config["layout"]
        
        # Format frontmatter
        if frontmatter_format == "toml":
            return self._format_toml_frontmatter(fm)
        elif frontmatter_format == "json":
            return self._format_json_frontmatter(fm)
        else:  # yaml (default)
            return self._format_yaml_frontmatter(fm)
    
    def _format_yaml_frontmatter(self, fm: dict) -> str:
        """Format YAML frontmatter."""
        lines = ["---"]
        for key, value in sorted(fm.items()):
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            elif isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")
        return "\n".join(lines)
    
    def _format_toml_frontmatter(self, fm: dict) -> str:
        """Format TOML frontmatter (Hugo style)."""
        lines = ["+++"]
        for key, value in sorted(fm.items()):
            if isinstance(value, list):
                lines.append(f"{key} = [{', '.join(repr(v) for v in value)}]")
            elif isinstance(value, dict):
                lines.append(f"{key} = {{ {', '.join(f'{k}={repr(v)}' for k, v in value.items())} }}")
            else:
                lines.append(f"{key} = {repr(value)}")
        lines.append("+++")
        return "\n".join(lines)
    
    def _format_json_frontmatter(self, fm: dict) -> str:
        """Format JSON frontmatter."""
        import json
        return f"<!--\n{json.dumps(fm, indent=2, default=str)}\n-->"
