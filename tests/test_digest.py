"""Tests for digest generation."""

import pytest
from datetime import datetime, timezone, timedelta

from digest_tracker.digest import DigestGenerator
from digest_tracker.db import Database, create_topic, create_source, save_articles, create_blog, link_blog_to_topic


class TestDigestGenerator:
    """Test digest generation functionality."""
    
    @pytest.fixture
    def generator(self, test_db):
        """Create a digest generator instance."""
        config = {
            "default_frequency": "weekly",
            "max_articles_per_digest": 50,
            "whatsapp": {
                "brief": True,
                "show_urls": True,
                "emoji_header": True
            }
        }
        return DigestGenerator(test_db, config)
    
    @pytest.fixture
    def populated_db(self, test_db, created_topic, created_source, sample_articles):
        """Populate database with sample data."""
        for article in sample_articles:
            article["source_id"] = created_source["id"]
        
        save_articles(test_db, sample_articles)
        yield test_db
    
    def test_generate_weekly_digest(self, generator, created_topic, populated_db):
        """Test generating a weekly digest."""
        result = generator.generate("test-topic", "weekly", 7)
        
        assert result is not None
        assert "digest_id" in result
        assert "content" in result
        assert "article_count" in result
        assert result["article_count"] == 3
        assert result["frequency"] == "weekly"
    
    def test_generate_daily_digest(self, generator, created_topic, populated_db):
        """Test generating a daily digest."""
        result = generator.generate("test-topic", "daily", 1)
        
        assert result is not None
        assert result["frequency"] == "daily"
    
    def test_generate_monthly_digest(self, generator, created_topic, populated_db):
        """Test generating a monthly digest."""
        result = generator.generate("test-topic", "monthly", 30)
        
        assert result is not None
        assert result["frequency"] == "monthly"
    
    def test_generate_with_date_range(self, generator, created_topic, populated_db):
        """Test generating digest with custom date range."""
        period_start = datetime.now(timezone.utc) - timedelta(hours=4)
        period_end = datetime.now(timezone.utc)
        
        result = generator.generate(
            "test-topic",
            "custom",
            0,
            since=period_start,
            until=period_end
        )
        
        assert result is not None
        # Should include articles within the 4-hour window
        assert result["article_count"] <= 3
    
    def test_generate_for_nonexistent_topic(self, generator):
        """Test generating digest for non-existent topic."""
        result = generator.generate("nonexistent", "weekly", 7)
        
        assert result is None
    
    def test_generate_empty_digest(self, generator, created_topic):
        """Test generating digest when no articles exist."""
        result = generator.generate("test-topic", "weekly", 7)
        
        assert result is not None
        assert result["article_count"] == 0
    
    def test_digest_content_format(self, generator, created_topic, populated_db):
        """Test that digest content is properly formatted."""
        result = generator.generate("test-topic", "weekly", 7)
        
        content = result["content"]
        
        # Check for header
        assert "test-topic" in content.lower() or "Test Topic" in content
        
        # Check for article entries
        assert "Article 1" in content or "article1" in content
        assert "Article 2" in content or "article2" in content
    
    def test_digest_period_includes(self, generator, created_topic, populated_db):
        """Test that digest includes period information."""
        result = generator.generate("test-topic", "weekly", 7)
        
        assert "period" in result
        assert "start" in result["period"].lower() or "from" in result["period"].lower()
    
    def test_digest_saves_to_database(self, generator, created_topic, populated_db):
        """Test that digest is saved to database."""
        result = generator.generate("test-topic", "weekly", 7)
        
        digest = generator.db.get_digest_by_id(result["digest_id"])
        assert digest is not None
        assert digest["topic_id"] == created_topic["id"]
        assert digest["frequency"] == "weekly"
        assert digest["article_count"] == 3
    
    def test_max_articles_limit(self, generator, created_topic, populated_db):
        """Test that max_articles_per_digest limit is respected."""
        # Set a low limit
        generator.config["max_articles_per_digest"] = 2
        
        result = generator.generate("test-topic", "weekly", 7)
        
        assert result["article_count"] <= 2
    
    def test_emoji_header_format(self, generator, created_topic, populated_db):
        """Test that emoji headers are included when configured."""
        generator.config["whatsapp"]["emoji_header"] = True
        
        result = generator.generate("test-topic", "weekly", 7)
        
        content = result["content"]
        # Should contain some emojis
        assert any(emoji in content for emoji in ["📊", "📰", "🔥", "📄", "✓"])
    
    def test_brief_format(self, generator, created_topic, populated_db):
        """Test brief format for digests."""
        generator.config["whatsapp"]["brief"] = True
        
        result = generator.generate("test-topic", "weekly", 7)
        
        content = result["content"]
        # Brief format should show summaries, not full content
        assert "Summary 1" in content or "Content of article 1" in content
    
    def test_urls_shown(self, generator, created_topic, populated_db):
        """Test that URLs are shown when configured."""
        generator.config["whatsapp"]["show_urls"] = True
        
        result = generator.generate("test-topic", "weekly", 7)
        
        content = result["content"]
        assert "https://example.com/article1" in content or "example.com" in content


class TestDigestFormatting:
    """Test digest formatting and output."""
    
    @pytest.fixture
    def generator(self, test_db):
        """Create a digest generator instance."""
        config = {
            "default_frequency": "weekly",
            "max_articles_per_digest": 50,
            "whatsapp": {
                "brief": True,
                "show_urls": True,
                "emoji_header": True
            }
        }
        return DigestGenerator(test_db, config)
    
    def test_format_period_weekly(self, generator):
        """Test formatting weekly period."""
        start = datetime(2026, 2, 17, tzinfo=timezone.utc)
        end = datetime(2026, 2, 23, tzinfo=timezone.utc)
        
        period_str = generator._format_period(start, end, "weekly")
        
        assert "Feb 17-23" in period_str or "17-23" in period_str
    
    def test_format_period_monthly(self, generator):
        """Test formatting monthly period."""
        start = datetime(2026, 2, 1, tzinfo=timezone.utc)
        end = datetime(2026, 2, 28, tzinfo=timezone.utc)
        
        period_str = generator._format_period(start, end, "monthly")
        
        assert "February 2026" in period_str or "Feb 2026" in period_str
    
    def test_format_period_daily(self, generator):
        """Test formatting daily period."""
        start = datetime(2026, 2, 24, tzinfo=timezone.utc)
        end = datetime(2026, 2, 24, tzinfo=timezone.utc)
        
        period_str = generator._format_period(start, end, "daily")
        
        assert "Feb 24" in period_str or "24" in period_str
