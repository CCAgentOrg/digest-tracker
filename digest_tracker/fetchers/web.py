"""Web page fetcher."""

import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional

from .base import BaseFetcher


class WebFetcher(BaseFetcher):
    """Fetch articles from web pages."""
    
    def fetch(
        self,
        url: str,
        since: Optional[datetime] = None,
        config: Optional[dict] = None
    ) -> list[dict]:
        """
        For web sources, we typically just fetch the page itself.
        For incremental fetching, we'd need to detect articles on the page.
        This is a simple implementation.
        """
        content = self.extract_content(url)
        
        # Try to extract article metadata
        metadata = self._extract_metadata(url)
        
        article = {
            "url": url,
            "title": metadata.get("title", ""),
            "content": content,
            "published_at": metadata.get("published_at"),
            "author": metadata.get("author", ""),
            "metadata": metadata
        }
        
        # Filter by date if specified
        if since:
            published = metadata.get("published_at")
            if published and published < since:
                return []
        
        return [article]
    
    def extract_content(self, url: str) -> str:
        """Extract main article content from a web page."""
        try:
            response = httpx.get(url, follow_redirects=True, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try common article containers
            for selector in [
                "article",
                '[class*="article"]',
                '[class*="post"]',
                '[class*="content"]',
                '[id*="article"]',
                '[id*="post"]',
                '[id*="content"]',
            ]:
                elements = soup.select(selector)
                if elements:
                    # Get the largest element
                    largest = max(elements, key=lambda e: len(e.get_text()))
                    return self._clean_text(largest.get_text())
            
            # Fallback: get main body content
            body = soup.find("body")
            if body:
                return self._clean_text(body.get_text())
            
            return ""
            
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return ""
    
    def _extract_metadata(self, url: str) -> dict:
        """Extract metadata from web page."""
        metadata = {}
        
        try:
            response = httpx.get(url, follow_redirects=True, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Title
            title = soup.find("title")
            if title:
                metadata["title"] = title.get_text().strip()
            
            # Meta tags
            for meta in soup.find_all("meta"):
                name = meta.get("name") or meta.get("property", "")
                content = meta.get("content", "")
                
                if name in ["author", "article:author"]:
                    metadata["author"] = content
                elif name in ["published_time", "article:published_time", "date"]:
                    metadata["published_at"] = self._parse_date(content)
                elif name in ["description", "og:description"]:
                    metadata["description"] = content
            
            # JSON-LD structured data
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if "headline" in data:
                            metadata["title"] = metadata.get("title") or data["headline"]
                        if "author" in data:
                            if isinstance(data["author"], dict):
                                metadata["author"] = data["author"].get("name")
                            elif isinstance(data["author"], list) and data["author"]:
                                metadata["author"] = data["author"][0].get("name")
                        if "datePublished" in data:
                            metadata["published_at"] = self._parse_date(data["datePublished"])
                except Exception:
                    pass
            
        except Exception as e:
            print(f"Error extracting metadata from {url}: {e}")
        
        return metadata
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except Exception:
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        import re
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]
        return "\n".join(lines)
