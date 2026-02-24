"""Tests for database operations."""

import pytest
from datetime import datetime, timezone, timedelta

from digest_tracker.db import (
    Database,
    create_topic,
    get_topic_by_name,
    list_topics,
    delete_topic,
    create_source,
    get_sources_for_topic,
    delete_source,
    save_articles,
    create_blog,
    list_blogs,
    get_blog_by_name,
    link_blog_to_topic,
    get_blog_for_topic,
    unlink_blog_from_topic,
    create_digest,
    get_digests_for_topic,
    get_digest_by_id,
    mark_digest_published,
    get_articles_for_digest
)


class TestTopicOperations:
    """Test topic CRUD operations."""
    
    def test_create_topic(self, test_db):
        """Test creating a new topic."""
        topic_id = create_topic(test_db, "test-topic", "Test description")
        assert topic_id is not None
        assert isinstance(topic_id, str)
    
    def test_get_topic_by_name(self, test_db, created_topic):
        """Test retrieving a topic by name."""
        topic = get_topic_by_name(test_db, "test-topic")
        assert topic is not None
        assert topic["name"] == "test-topic"
        assert topic["description"] == "Test topic description"
        assert topic["active"] == 1
    
    def test_get_nonexistent_topic(self, test_db):
        """Test retrieving a non-existent topic."""
        topic = get_topic_by_name(test_db, "nonexistent")
        assert topic is None
    
    def test_list_topics_empty(self, test_db):
        """Test listing topics when empty."""
        topics = list_topics(test_db)
        assert topics == []
    
    def test_list_topics(self, test_db):
        """Test listing multiple topics."""
        create_topic(test_db, "topic1", "Description 1")
        create_topic(test_db, "topic2", "Description 2")
        
        topics = list_topics(test_db)
        assert len(topics) == 2
        topic_names = [t["name"] for t in topics]
        assert "topic1" in topic_names
        assert "topic2" in topic_names
    
    def test_delete_topic(self, test_db, created_topic):
        """Test deleting (deactivating) a topic."""
        result = delete_topic(test_db, "test-topic")
        assert result is True
        
        # Verify it's deactivated
        topic = get_topic_by_name(test_db, "test-topic")
        assert topic is None  # Only returns active topics
    
    def test_delete_nonexistent_topic(self, test_db):
        """Test deleting a non-existent topic."""
        result = delete_topic(test_db, "nonexistent")
        assert result is False


class TestSourceOperations:
    """Test source CRUD operations."""
    
    def test_create_source(self, test_db, created_topic):
        """Test creating a new source."""
        source_id = create_source(
            test_db,
            created_topic["id"],
            "https://example.com/feed.xml",
            "rss",
            {"some": "config"}
        )
        assert source_id is not None
        assert isinstance(source_id, str)
    
    def test_get_sources_for_topic(self, test_db, created_source):
        """Test retrieving sources for a topic."""
        sources = get_sources_for_topic(test_db, "test-topic")
        assert len(sources) == 1
        assert sources[0]["url"] == "https://example.com/feed.xml"
        assert sources[0]["source_type"] == "rss"
    
    def test_get_sources_for_nonexistent_topic(self, test_db):
        """Test retrieving sources for a non-existent topic."""
        sources = get_sources_for_topic(test_db, "nonexistent")
        assert sources == []
    
    def test_delete_source(self, test_db, created_source):
        """Test deleting a source."""
        result = delete_source(test_db, created_source["id"])
        assert result is True
        
        sources = get_sources_for_topic(test_db, "test-topic")
        assert len(sources) == 0
    
    def test_delete_nonexistent_source(self, test_db):
        """Test deleting a non-existent source."""
        result = delete_source(test_db, "nonexistent-id")
        assert result is False


class TestArticleOperations:
    """Test article operations."""
    
    def test_save_articles(self, test_db, created_source, sample_articles):
        """Test saving articles to database."""
        for article in sample_articles:
            article["source_id"] = created_source["id"]
        
        saved = save_articles(test_db, sample_articles)
        assert saved == 3
    
    def test_save_duplicate_articles(self, test_db, created_source, sample_articles):
        """Test that duplicate articles are not saved."""
        for article in sample_articles:
            article["source_id"] = created_source["id"]
        
        # Save first time
        saved1 = save_articles(test_db, sample_articles)
        assert saved1 == 3
        
        # Try to save again (duplicates)
        saved2 = save_articles(test_db, sample_articles)
        assert saved2 == 0
    
    def test_get_articles_for_digest(self, test_db, created_source, created_topic, sample_articles):
        """Test retrieving articles for digest generation."""
        for article in sample_articles:
            article["source_id"] = created_source["id"]
        
        save_articles(test_db, sample_articles)
        
        articles = get_articles_for_digest(test_db, created_topic["id"])
        assert len(articles) == 3
    
    def test_get_articles_with_date_filter(self, test_db, created_source, created_topic, sample_articles):
        """Test filtering articles by date."""
        for article in sample_articles:
            article["source_id"] = created_source["id"]
        
        save_articles(test_db, sample_articles)
        
        # Get articles from last 2 hours
        since = datetime.now(timezone.utc) - timedelta(hours=2)
        articles = get_articles_for_digest(test_db, created_topic["id"], since=since)
        assert len(articles) == 1


class TestBlogOperations:
    """Test blog CRUD operations."""
    
    def test_create_blog(self, test_db):
        """Test creating a new blog."""
        blog_id = create_blog(
            test_db,
            "test-blog",
            "local",
            {"path": "/tmp/test"}
        )
        assert blog_id is not None
        assert isinstance(blog_id, str)
    
    def test_list_blogs(self, test_db, created_blog):
        """Test listing all blogs."""
        create_blog(test_db, "another-blog", "local", {"path": "/tmp/another"})
        
        blogs = list_blogs(test_db)
        assert len(blogs) == 2
        blog_names = [b["name"] for b in blogs]
        assert "test-blog" in blog_names
        assert "another-blog" in blog_names
    
    def test_get_blog_by_name(self, test_db, created_blog):
        """Test retrieving a blog by name."""
        blog = get_blog_by_name(test_db, "test-blog")
        assert blog is not None
        assert blog["name"] == "test-blog"
        assert blog["blog_type"] == "local"
        assert blog["config"]["path"] == "/tmp/test-blog"
    
    def test_link_blog_to_topic(self, test_db, created_topic, created_blog):
        """Test linking a blog to a topic."""
        result = link_blog_to_topic(
            test_db,
            "test-topic",
            "test-blog",
            category="test",
            slug_prefix="test/"
        )
        assert result is True
    
    def test_get_blog_for_topic(self, test_db, created_topic, created_blog):
        """Test retrieving the blog linked to a topic."""
        link_blog_to_topic(test_db, "test-topic", "test-blog")
        
        blog = get_blog_for_topic(test_db, "test-topic")
        assert blog is not None
        assert blog["name"] == "test-blog"
    
    def test_unlink_blog_from_topic(self, test_db, created_topic, created_blog):
        """Test unlinking a blog from a topic."""
        link_blog_to_topic(test_db, "test-topic", "test-blog")
        
        result = unlink_blog_from_topic(test_db, "test-topic")
        assert result is True
        
        blog = get_blog_for_topic(test_db, "test-topic")
        assert blog is None


class TestDigestOperations:
    """Test digest operations."""
    
    def test_create_digest(self, test_db, created_topic, created_blog):
        """Test creating a digest."""
        period_start = datetime.now(timezone.utc) - timedelta(days=7)
        period_end = datetime.now(timezone.utc)
        
        digest_id = create_digest(
            test_db,
            created_topic["id"],
            "weekly",
            period_start,
            period_end,
            "Test content",
            "Test summary",
            10,
            created_blog["id"]
        )
        assert digest_id is not None
    
    def test_get_digests_for_topic(self, test_db, created_topic):
        """Test retrieving digests for a topic."""
        period_start = datetime.now(timezone.utc) - timedelta(days=7)
        period_end = datetime.now(timezone.utc)
        
        create_digest(
            test_db,
            created_topic["id"],
            "weekly",
            period_start,
            period_end,
            "Content 1",
            "Summary 1",
            5
        )
        
        create_digest(
            test_db,
            created_topic["id"],
            "daily",
            period_start,
            period_end,
            "Content 2",
            "Summary 2",
            2
        )
        
        digests = get_digests_for_topic(test_db, "test-topic")
        assert len(digests) == 2
    
    def test_get_digest_by_id(self, test_db, created_topic):
        """Test retrieving a digest by ID."""
        period_start = datetime.now(timezone.utc) - timedelta(days=7)
        period_end = datetime.now(timezone.utc)
        
        digest_id = create_digest(
            test_db,
            created_topic["id"],
            "weekly",
            period_start,
            period_end,
            "Test content",
            "Test summary",
            5
        )
        
        digest = get_digest_by_id(test_db, digest_id)
        assert digest is not None
        assert digest["content"] == "Test content"
        assert digest["article_count"] == 5
    
    def test_mark_digest_published(self, test_db, created_topic):
        """Test marking a digest as published."""
        period_start = datetime.now(timezone.utc) - timedelta(days=7)
        period_end = datetime.now(timezone.utc)
        
        digest_id = create_digest(
            test_db,
            created_topic["id"],
            "weekly",
            period_start,
            period_end,
            "Test content",
            "Test summary",
            5
        )
        
        result = mark_digest_published(test_db, digest_id, "https://example.com/published")
        assert result is True
        
        digest = get_digest_by_id(test_db, digest_id)
        assert digest["published"] == 1
        assert digest["published_url"] == "https://example.com/published"


class TestDatabase:
    """Test database connection and setup."""
    
    def test_database_creates_tables(self, test_db):
        """Test that all tables are created."""
        # Just query each table to ensure it exists
        tables = ["topics", "sources", "articles", "blogs", "topic_blogs", "digests", "schedules"]
        for table in tables:
            result = test_db.execute(f"SELECT COUNT(*) FROM {table}", fetch=True)
            assert result is not None
    
    def test_json_loads_dumps(self, test_db):
        """Test JSON serialization helpers."""
        data = {"key": "value", "nested": {"a": 1}}
        json_str = test_db.json_dumps(data)
        assert json_str is not None
        
        loaded = test_db.json_loads(json_str)
        assert loaded == data
    
    def test_json_loads_null(self, test_db):
        """Test JSON loads with None."""
        assert test_db.json_loads(None) is None
    
    def test_json_dumps_none(self, test_db):
        """Test JSON dumps with None."""
        assert test_db.json_dumps(None) is None
