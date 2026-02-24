"""Digest generation and formatting."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from .db import Database, get_articles_for_digest, create_digest
from .utils import format_date, slugify


class DigestGenerator:
    """Generate digests from fetched articles."""
    
    def __init__(self, db: Database, config: dict):
        self.db = db
        self.config = config
    
    def generate(
        self,
        topic_name: str,
        frequency: str = "weekly",
        days: int = 7,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Optional[dict]:
        """Generate a digest for a topic."""
        from .db import get_topic_by_name, get_blog_for_topic
        
        topic = get_topic_by_name(self.db, topic_name)
        if not topic:
            print(f"Topic not found: {topic_name}")
            return None
        
        # Calculate date range
        if not until:
            until = datetime.now(timezone.utc)
        if not since:
            since = until - timedelta(days=days)
        
        # Get articles
        articles = get_articles_for_digest(self.db, topic["id"], since)
        
        if not articles:
            print(f"No articles found for {topic_name} in this period")
            return None
        
        # Limit articles
        max_articles = self.config.get("max_articles_per_digest", 50)
        articles = articles[:max_articles]
        
        # Generate digest content
        content = self._format_content(topic, articles, frequency, since, until)
        summary = self._generate_summary(articles)
        
        # Save digest
        blog = get_blog_for_topic(self.db, topic_name)
        blog_id = blog["id"] if blog else None
        
        digest_id = create_digest(
            self.db,
            topic["id"],
            frequency,
            since,
            until,
            content,
            summary,
            len(articles),
            blog_id
        )
        
        return {
            "digest_id": digest_id,
            "topic": topic["name"],
            "frequency": frequency,
            "period": f"{format_date(since)} - {format_date(until)}",
            "article_count": len(articles),
            "content": content,
            "summary": summary
        }
    
    def _format_content(
        self,
        topic: dict,
        articles: list[dict],
        frequency: str,
        since: datetime,
        until: datetime
    ) -> str:
        """Format digest content."""
        # Use WhatsApp format by default
        return self._format_whatsapp(topic, articles, frequency, since, until)
    
    def _format_whatsapp(
        self,
        topic: dict,
        articles: list[dict],
        frequency: str,
        since: datetime,
        until: datetime
    ) -> str:
        """Format digest for WhatsApp."""
        lines = []
        
        # Header
        emoji = "📊"
        period = f"Week of {since.strftime('%b %d')} - {until.strftime('%b %d')}" if frequency == "weekly" else f"{since.strftime('%b %d')}"
        lines.append(f"{emoji} *{topic['name'].title()} Digest — {period}*")
        lines.append("")
        
        # Summary
        summary = self._generate_summary(articles)
        lines.append(f"*{len(articles)} articles tracked*")
        lines.append("")
        
        # Top stories (first 3)
        if len(articles) >= 3:
            lines.append("*🔥 Top Stories*")
            for i, article in enumerate(articles[:3], 1):
                title = article.get("title", "No title")[:60]
                source = article.get("metadata", {}).get("source", "")
                lines.append(f"{i}. {title}… ({source})")
            lines.append("")
        
        # Articles list
        lines.append(f"*📄 Articles ({len(articles)})*")
        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            url = article.get("url", "")
            published = article.get("published_at")
            
            date_str = ""
            if published:
                try:
                    pub_date = datetime.fromisoformat(published)
                    date_str = f" — {pub_date.strftime('%b %d')}"
                except Exception:
                    pass
            
            lines.append(f"{i}. *{title}*{date_str}")
            
            # Add summary if available
            summary_text = article.get("summary", "")
            if summary_text and summary_text != article.get("content", ""):
                lines.append(f"   → {summary_text[:100]}…")
            
            if self.config.get("show_urls", True):
                lines.append(f"   {url}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_markdown(
        self,
        topic: dict,
        articles: list[dict],
        frequency: str,
        since: datetime,
        until: datetime
    ) -> str:
        """Format digest as Markdown for blog posts."""
        lines = []
        
        # Frontmatter
        frontmatter = {
            "title": f"{topic['name'].title()} {frequency.title()} Digest — {since.strftime('%b %d')}, {since.year}",
            "date": until.strftime("%Y-%m-%d"),
            "tags": [topic['name'], "digest", frequency]
        }
        
        lines.append("---")
        for key, value in frontmatter.items():
            if isinstance(value, list):
                lines.append(f"{key}: {value}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")
        lines.append("")
        
        # Title
        period = f"Week ending {until.strftime('%B %d, %Y')}" if frequency == "weekly" else f"{until.strftime('%B %d, %Y')}"
        lines.append(f"# {topic['name'].title()} {frequency.title()} Digest")
        lines.append("")
        lines.append(f"*{period} | {len(articles)} articles tracked*")
        lines.append("")
        
        # Summary
        summary = self._generate_summary(articles)
        lines.append("## Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")
        
        # Top stories
        if len(articles) >= 3:
            lines.append("## Top Stories")
            lines.append("")
            for article in articles[:3]:
                title = article.get("title", "No title")
                source = article.get("metadata", {}).get("source", "")
                lines.append(f"### {title}")
                lines.append("")
                lines.append(f"*Source*: {source}")
                lines.append("")
        
        # All articles
        lines.append("## All Articles")
        lines.append("")
        for article in articles:
            title = article.get("title", "No title")
            url = article.get("url", "")
            published = article.get("published_at")
            source = article.get("metadata", {}).get("source", "")
            
            lines.append(f"### {title}")
            lines.append("")
            
            if published:
                try:
                    pub_date = datetime.fromisoformat(published)
                    lines.append(f"*Published*: {pub_date.strftime('%B %d, %Y')}")
                except Exception:
                    pass
            
            lines.append(f"*Source*: {source}")
            lines.append("")
            lines.append(url)
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_summary(self, articles: list[dict]) -> str:
        """Generate a summary of articles."""
        if not articles:
            return "No articles to summarize."
        
        # Group by source
        by_source = {}
        for article in articles:
            source = article.get("metadata", {}).get("source", "Unknown")
            by_source[source] = by_source.get(source, 0) + 1
        
        # Build summary
        parts = []
        parts.append(f"Tracked {len(articles)} article{'s' if len(articles) > 1 else ''}")
        
        if by_source:
            sources = [f"{count} from {src}" for src, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True)[:3]]
            if len(by_source) > 3:
                sources.append(f"and {len(by_source) - 3} more")
            parts.append(" from " + ", ".join(sources))
        
        return "".join(parts)
