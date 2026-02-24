"""Fixtures for digest-tracker tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

from digest_tracker.db import Database, create_topic, create_source, create_blog, link_blog_to_topic


@pytest.fixture
def temp_dir():
    """Temporary directory for test databases."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def test_db(temp_dir):
    """Test database instance."""
    db_path = str(Path(temp_dir) / "test.db")
    db = Database(database_url=f"file:{db_path}")
    yield db


@pytest.fixture
def sample_topic():
    """Sample topic for testing."""
    return {
        "id": "topic-123",
        "name": "test-topic",
        "description": "Test topic description"
    }


@pytest.fixture
def created_topic(test_db):
    """Create a topic in the database."""
    topic_id = create_topic(
        test_db,
        "test-topic",
        "Test topic description"
    )
    return {
        "id": topic_id,
        "name": "test-topic",
        "description": "Test topic description"
    }


@pytest.fixture
def sample_source():
    """Sample source for testing."""
    return {
        "url": "https://example.com/feed.xml",
        "source_type": "rss",
        "config": None
    }


@pytest.fixture
def created_source(test_db, created_topic, sample_source):
    """Create a source in the database."""
    source_id = create_source(
        test_db,
        created_topic["id"],
        sample_source["url"],
        sample_source["source_type"],
        sample_source["config"]
    )
    return {**sample_source, "id": source_id, "topic_id": created_topic["id"]}


@pytest.fixture
def created_blog(test_db):
    """Create a blog in the database."""
    blog_id = create_blog(
        test_db,
        "test-blog",
        "local",
        {"path": "/tmp/test-blog"}
    )
    return {
        "id": blog_id,
        "name": "test-blog",
        "blog_type": "local",
        "config": {"path": "/tmp/test-blog"}
    }


@pytest.fixture
def sample_articles():
    """Sample articles for testing."""
    base_time = datetime.now(timezone.utc)
    return [
        {
            "url": "https://example.com/article1",
            "title": "Article 1",
            "content": "Content of article 1",
            "published_at": (base_time - timedelta(hours=1)).isoformat(),
            "author": "Author 1",
            "summary": "Summary 1",
            "metadata": {"source": "Test Feed"}
        },
        {
            "url": "https://example.com/article2",
            "title": "Article 2",
            "content": "Content of article 2",
            "published_at": (base_time - timedelta(hours=2)).isoformat(),
            "author": "Author 2",
            "summary": "Summary 2",
            "metadata": {"source": "Test Feed"}
        },
        {
            "url": "https://example.com/article3",
            "title": "Article 3",
            "content": "Content of article 3",
            "published_at": (base_time - timedelta(hours=3)).isoformat(),
            "author": "Author 3",
            "summary": "Summary 3",
            "metadata": {"source": "Test Feed"}
        }
    ]


@pytest.fixture
def rss_feed_sample():
    """Sample RSS feed response."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <link>https://example.com</link>
    <description>Test RSS Feed</description>
    <item>
      <title>Article 1</title>
      <link>https://example.com/article1</link>
      <description>Content of article 1</description>
      <pubDate>Mon, 24 Feb 2026 10:00:00 GMT</pubDate>
      <author>Author 1</author>
    </item>
    <item>
      <title>Article 2</title>
      <link>https://example.com/article2</link>
      <description>Content of article 2</description>
      <pubDate>Mon, 24 Feb 2026 09:00:00 GMT</pubDate>
      <author>Author 2</author>
    </item>
  </channel>
</rss>
"""


@pytest.fixture
def html_page_sample():
    """Sample HTML page response."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Article Page</title>
</head>
<body>
    <article>
        <h1>Main Title</h1>
        <p>This is the main content of the article.</p>
        <p>Second paragraph with more content.</p>
    </article>
</body>
</html>
"""
