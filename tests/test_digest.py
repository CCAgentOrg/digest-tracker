"""Tests for digest generation and formatting."""

import pytest
from datetime import datetime, timedelta, timezone

from digest_tracker.digest import DigestGenerator
from digest_tracker.db import Database, create_topic, create_source, save_articles, get_articles_for_digest, create_digest
from digest_tracker.utils import generate_id


@pytest.fixture
def temp_dir():
    """Temporary directory for test databases."""
    import tempfile
    import shutil
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def test_db(temp_dir):
    """Test database instance."""
    db = Database(database_url=f"file:{temp_dir}/test.db")
    yield db


@pytest.fixture
def generator(test_db):
    """Digest generator instance."""
    config = {
        "max_articles_per_digest": 50,
        "show_urls": True,
        "emoji_header": True
    }
    return DigestGenerator(test_db, config)


@pytest.fixture
def created_topic(test_db):
    """Create a topic in the database."""
    topic_id = generate_id("test-topic")
    test_db.execute(
        "INSERT INTO topics (id, name, description) VALUES (?, ?, ?)",
        (topic_id, "test-topic", "Test topic description")
    )
    return {
        "id": topic_id,
        "name": "test-topic",
        "description": "Test topic description"
    }


@pytest.fixture
def created_source(test_db, created_topic):
    """Create a source in the database."""
    source_id = generate_id(f"{created_topic['id']}-https://example.com/feed.xml")
    test_db.execute(
        "INSERT INTO sources (id, topic_id, url, source_type) VALUES (?, ?, ?, ?)",
        (source_id, created_topic["id"], "https://example.com/feed.xml", "rss")
    )
    return {
        "id": source_id,
        "topic_id": created_topic["id"],
        "url": "https://example.com/feed.xml",
        "source_type": "rss"
    }


@pytest.fixture
def sample_articles(created_source):
    """Sample articles for testing."""
    base_time = datetime.now(timezone.utc)
    return [
        {
            "source_id": created_source["id"],
            "url": "https://example.com/article1",
            "title": "Article 1",
            "content": "Content of article 1",
            "published_at": (base_time - timedelta(hours=1)).isoformat(),
            "author": "Author 1",
            "summary": "Summary 1",
            "metadata": {"source": "Test Feed"}
        },
        {
            "source_id": created_source["id"],
            "url": "https://example.com/article2",
            "title": "Article 2",
            "content": "Content of article 2",
            "published_at": (base_time - timedelta(hours=2)).isoformat(),
            "author": "Author 2",
            "summary": "Summary 2",
            "metadata": {"source": "Test Feed"}
        },
        {
            "source_id": created_source["id"],
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
def populated_db(test_db, created_topic, created_source, sample_articles):
    """Database populated with articles."""
    save_articles(test_db, sample_articles)
    return test_db


class TestDigestGenerator:
    """Test DigestGenerator class."""
    
    def test_generate_weekly_digest(self, generator, created_topic, populated_db):
        """Test generating weekly digest."""
        result = generator.generate("test-topic", "weekly", 7)
        
        assert result is not None
        assert result["topic"] == "test-topic"
        assert result["frequency"] == "weekly"
        assert result["article_count"] == 3
        assert "content" in result
        assert "summary" in result
    
    def test_generate_daily_digest(self, generator, created_topic, populated_db):
        """Test generating daily digest."""
        result = generator.generate("test-topic", "daily", 1)
        
        assert result is not None
        assert result["frequency"] == "daily"
        assert result["article_count"] == 3
    
    def test_generate_monthly_digest(self, generator, created_topic, populated_db):
        """Test generating monthly digest."""
        result = generator.generate("test-topic", "monthly", 30)
        
        assert result is not None
        assert result["frequency"] == "monthly"
        assert result["article_count"] == 3
    
    def test_generate_with_date_range(self, generator, created_topic, populated_db):
        """Test generating digest with custom date range."""
        since = datetime.now(timezone.utc) - timedelta(days=2)
        until = datetime.now(timezone.utc)
        
        result = generator.generate("test-topic", "custom", days=0, since=since, until=until)
        
        assert result is not None
        assert result["frequency"] == "custom"
    
    def test_generate_for_nonexistent_topic(self, generator):
        """Test generating digest for nonexistent topic."""
        result = generator.generate("nonexistent", "weekly")
        
        assert result is None
    
    def test_generate_empty_digest(self, generator, created_topic):
        """Test generating digest when no articles exist."""
        result = generator.generate("test-topic", "weekly", 7)
        
        # Returns None when no articles found
        assert result is None
    
    def test_digest_content_format(self, generator, created_topic, populated_db):
        """Test that digest content is formatted correctly."""
        result = generator.generate("test-topic", "weekly", 7)
        
        content = result["content"]
        
        # Check for WhatsApp formatting
        assert "test-topic" in content.lower() or "Test-Topic" in content
        assert "📊" in content or "*" in content  # Emoji or markdown
        assert "Article" in content  # Articles should be listed
    
    def test_digest_period_includes(self, generator, created_topic, populated_db):
        """Test that digest includes period information."""
        result = generator.generate("test-topic", "weekly", 7)
        
        # Period should include date information
        assert "period" in result
        assert "-" in result["period"]  # Date range separator
    
    def test_digest_saves_to_database(self, generator, created_topic, populated_db):
        """Test that digest is saved to database."""
        result = generator.generate("test-topic", "weekly", 7)
        
        # Check digest was saved
        from digest_tracker.db import get_digests_for_topic
        digests = get_digests_for_topic(generator.db, "test-topic")
        
        assert len(digests) > 0
        assert digests[0]["frequency"] == "weekly"
        assert digests[0]["article_count"] == 3
    
    def test_max_articles_limit(self, generator, created_topic, sample_articles, created_source):
        """Test that max_articles limit is respected."""
        # Create many articles
        many_articles = []
        base_time = datetime.now(timezone.utc)
        for i in range(100):
            many_articles.append({
                "source_id": created_source["id"],
                "url": f"https://example.com/article{i}",
                "title": f"Article {i}",
                "content": f"Content {i}",
                "published_at": (base_time - timedelta(hours=i)).isoformat(),
                "author": f"Author {i}",
                "summary": f"Summary {i}",
                "metadata": {"source": "Test Feed"}
            })
        
        save_articles(generator.db, many_articles)
        
        # Generate with limit
        generator.config["max_articles_per_digest"] = 10
        result = generator.generate("test-topic", "weekly", 7)
        
        assert result["article_count"] == 10
    
    def test_emoji_header_format(self, generator, created_topic, populated_db):
        """Test emoji header formatting."""
        result = generator.generate("test-topic", "weekly", 7)
        
        assert "📊" in result["content"]
    
    def test_brief_format(self, generator, created_topic, populated_db):
        """Test brief digest format."""
        generator.config["show_urls"] = False
        result = generator.generate("test-topic", "weekly", 7)
        
        assert result["article_count"] == 3
        # Content should still be generated
        assert "Article" in result["content"]
    
    def test_urls_shown(self, generator, created_topic, populated_db):
        """Test that URLs are shown when configured."""
        generator.config["show_urls"] = True
        result = generator.generate("test-topic", "weekly", 7)
        
        content = result["content"]
        # At least one URL should be present
        assert "https://" in content or "http://" in content


class TestDigestFormatting:
    """Test digest formatting methods."""
    
    def test_generate_summary(self, generator, sample_articles):
        """Test summary generation."""
        summary = generator._generate_summary(sample_articles)
        
        assert "3" in summary  # Article count
        assert "article" in summary.lower()
    
    def test_generate_summary_empty(self, generator):
        """Test summary with no articles."""
        summary = generator._generate_summary([])
        
        assert "no article" in summary.lower()
