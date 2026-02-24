"""Tests for content fetchers."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from digest_tracker.fetchers import RSSFetcher, WebFetcher, get_fetcher


class TestRSSFetcher:
    """Test RSS feed fetcher."""
    
    def test_get_fetcher_rss(self):
        """Test getting RSS fetcher."""
        fetcher = get_fetcher("rss")
        assert isinstance(fetcher, RSSFetcher)
    
    def test_get_fetcher_invalid(self):
        """Test getting invalid fetcher type."""
        with pytest.raises(ValueError, match="Unknown source type"):
            get_fetcher("invalid")
    
    @patch('digest_tracker.fetchers.rss.feedparser.parse')
    def test_fetch_rss_articles(self, mock_parse, rss_feed_sample):
        """Test fetching articles from RSS feed."""
        # Mock feedparser response
        mock_feed = MagicMock()
        mock_feed.feed.title = "Test Feed"
        mock_feed.entries = [
            MagicMock(
                link="https://example.com/article1",
                title="Article 1",
                description="Content of article 1",
                published_parsed=(2026, 2, 24, 10, 0, 0, 0, 55, 0),
                author="Author 1",
                tags=[]
            ),
            MagicMock(
                link="https://example.com/article2",
                title="Article 2",
                description="Content of article 2",
                published_parsed=(2026, 2, 24, 9, 0, 0, 0, 55, 0),
                author="Author 2",
                tags=[]
            )
        ]
        mock_parse.return_value = mock_feed
        
        fetcher = RSSFetcher()
        articles = fetcher.fetch("https://example.com/feed.xml")
        
        assert len(articles) == 2
        assert articles[0]["title"] == "Article 1"
        assert articles[0]["url"] == "https://example.com/article1"
        assert articles[0]["author"] == "Author 1"
        assert articles[0]["metadata"]["source"] == "Test Feed"
    
    @patch('digest_tracker.fetchers.rss.feedparser.parse')
    def test_fetch_rss_with_date_filter(self, mock_parse):
        """Test fetching RSS articles with date filtering."""
        since = datetime(2026, 2, 24, 8, 0, 0, tzinfo=timezone.utc)
        
        mock_feed = MagicMock()
        mock_feed.feed.title = "Test Feed"
        mock_feed.entries = [
            # Within date range
            MagicMock(
                link="https://example.com/recent",
                title="Recent Article",
                description="Recent content",
                published_parsed=(2026, 2, 24, 9, 0, 0, 0, 55, 0),
                author="Author",
                tags=[]
            ),
            # Outside date range
            MagicMock(
                link="https://example.com/old",
                title="Old Article",
                description="Old content",
                published_parsed=(2026, 2, 23, 7, 0, 0, 0, 55, 0),
                author="Author",
                tags=[]
            )
        ]
        mock_parse.return_value = mock_feed
        
        fetcher = RSSFetcher()
        articles = fetcher.fetch("https://example.com/feed.xml", since=since)
        
        assert len(articles) == 1
        assert articles[0]["title"] == "Recent Article"
    
    @patch('digest_tracker.fetchers.rss.feedparser.parse')
    def test_fetch_rss_with_tags(self, mock_parse):
        """Test that tags are extracted from RSS entries."""
        mock_feed = MagicMock()
        mock_feed.feed.title = "Test Feed"
        mock_feed.entries = [
            MagicMock(
                link="https://example.com/article",
                title="Article",
                description="Content",
                published_parsed=(2026, 2, 24, 10, 0, 0, 0, 55, 0),
                author="Author",
                tags=[MagicMock(term="tech"), MagicMock(term="news")]
            )
        ]
        mock_parse.return_value = mock_feed
        
        fetcher = RSSFetcher()
        articles = fetcher.fetch("https://example.com/feed.xml")
        
        assert "tech" in articles[0]["metadata"]["tags"]
        assert "news" in articles[0]["metadata"]["tags"]
    
    @patch('digest_tracker.fetchers.rss.feedparser.parse')
    def test_fetch_rss_handles_missing_fields(self, mock_parse):
        """Test handling of missing optional fields."""
        mock_feed = MagicMock()
        mock_feed.feed.title = "Test Feed"
        mock_feed.entries = [
            MagicMock(
                link="https://example.com/article",
                title="Article",
                # No description, author, or published date
                tags=[]
            )
        ]
        # Remove description attribute
        del mock_feed.entries[0].description
        mock_parse.return_value = mock_feed
        
        fetcher = RSSFetcher()
        articles = fetcher.fetch("https://example.com/feed.xml")
        
        assert len(articles) == 1
        assert articles[0]["title"] == "Article"
        assert articles[0]["author"] == ""
        assert articles[0]["published_at"] is None
    
    @patch('digest_tracker.fetchers.rss.feedparser.parse')
    def test_fetch_rss_error_handling(self, mock_parse):
        """Test error handling when RSS feed fails."""
        mock_parse.side_effect = Exception("Network error")
        
        fetcher = RSSFetcher()
        articles = fetcher.fetch("https://example.com/feed.xml")
        
        assert articles == []


class TestWebFetcher:
    """Test web page fetcher."""
    
    def test_get_fetcher_web(self):
        """Test getting web fetcher."""
        fetcher = get_fetcher("web")
        assert isinstance(fetcher, WebFetcher)
    
    @patch('digest_tracker.fetchers.web.httpx.get')
    def test_fetch_web_page(self, mock_get, html_page_sample):
        """Test fetching content from a web page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_page_sample
        mock_get.return_value = mock_response
        
        fetcher = WebFetcher()
        articles = fetcher.fetch("https://example.com/article")
        
        assert len(articles) == 1
        assert "Main Title" in articles[0]["title"]
        assert "main content of the article" in articles[0]["content"]
    
    @patch('digest_tracker.fetchers.web.httpx.get')
    def test_fetch_web_handles_404(self, mock_get):
        """Test handling of 404 errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        fetcher = WebFetcher()
        articles = fetcher.fetch("https://example.com/notfound")
        
        assert articles == []
    
    @patch('digest_tracker.fetchers.web.httpx.get')
    def test_extract_content_from_html(self, mock_get, html_page_sample):
        """Test extracting content from HTML."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_page_sample
        mock_get.return_value = mock_response
        
        fetcher = WebFetcher()
        content = fetcher.extract_content("https://example.com/article")
        
        assert "Main Title" in content
        assert "main content of the article" in content
    
    @patch('digest_tracker.fetchers.web.httpx.get')
    def test_extract_content_with_article_tag(self, mock_get):
        """Test extracting content from article-tagged HTML."""
        html = """<!DOCTYPE html>
        <html>
        <body>
            <nav>Navigation</nav>
            <article>
                <h1>Article Title</h1>
                <p>Article content here.</p>
            </article>
            <footer>Footer</footer>
        </body>
        </html>
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_get.return_value = mock_response
        
        fetcher = WebFetcher()
        content = fetcher.extract_content("https://example.com/article")
        
        assert "Article Title" in content
        assert "Article content here" in content
        assert "Navigation" not in content or "Navigation" not in content.lower()
        assert "Footer" not in content or "Footer" not in content.lower()
    
    @patch('digest_tracker.fetchers.web.httpx.get')
    def test_extract_content_fallback(self, mock_get):
        """Test content extraction fallback for non-structured pages."""
        html = """<!DOCTYPE html>
        <html>
        <head><title>Page Title</title></head>
        <body>
            <h1>Main Heading</h1>
            <p>Some paragraph text.</p>
        </body>
        </html>
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_get.return_value = mock_response
        
        fetcher = WebFetcher()
        content = fetcher.extract_content("https://example.com/simple")
        
        assert "Main Heading" in content
        assert "Some paragraph text" in content
