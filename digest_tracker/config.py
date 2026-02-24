"""Configuration management for digest-tracker."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class TursoConfig(BaseModel):
    database_url: str
    auth_token: Optional[str] = None


class WhatsAppConfig(BaseModel):
    brief: bool = True
    show_urls: bool = True
    emoji_header: bool = True


class BlogTemplateConfig(BaseModel):
    frontmatter_format: str = "yaml"
    include_tags: bool = True
    sections: list[str] = Field(default_factory=lambda: ["summary", "top_stories", "by_theme", "articles"])


class DigestConfig(BaseModel):
    default_frequency: str = "weekly"
    default_timezone: str = "Asia/Kolkata"
    max_articles_per_digest: int = 50
    whatsapp: WhatsAppConfig = Field(default_factory=WhatsAppConfig)
    blog_template: BlogTemplateConfig = Field(default_factory=BlogTemplateConfig)


class Config(BaseModel):
    turso: TursoConfig
    digests: DigestConfig = Field(default_factory=DigestConfig)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        if path is None:
            path = Path.home() / ".config" / "digest-tracker" / "config.yml"
        
        if not path.exists():
            # Create default config from environment
            return cls(
                turso=TursoConfig(
                    database_url=os.getenv("TURSO_DATABASE_URL", ""),
                    auth_token=os.getenv("TURSO_AUTH_TOKEN")
                )
            )
        
        with open(path) as f:
            data = yaml.safe_load(f)
        
        # Expand environment variables
        def expand_env_vars(obj):
            if isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                default = ""
                if ":" in env_var:
                    env_var, default = env_var.split(":", 1)
                return os.getenv(env_var, default)
            elif isinstance(obj, dict):
                return {k: expand_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [expand_env_vars(v) for v in obj]
            return obj
        
        data = expand_env_vars(data)
        return cls(**data)

    def save(self, path: Optional[Path] = None) -> None:
        if path is None:
            path = Path.home() / ".config" / "digest-tracker" / "config.yml"
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            yaml.dump(self.model_dump(exclude_none=True), f, default_flow_style=False)
