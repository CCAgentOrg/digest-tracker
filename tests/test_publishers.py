"""Tests for blog publishers."""

import pytest
import tempfile
import shutil
from pathlib import Path

from digest_tracker.publishers.local import LocalPublisher
from digest_tracker.publishers import get_publisher


@pytest.fixture
def temp_blog_dir():
    """Temporary directory for test blogs."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


class TestLocalPublisher:
    """Test LocalPublisher class."""
    
    def test_get_publisher_local(self):
        """Test getting local publisher."""
        publisher = get_publisher("local")
        assert isinstance(publisher, LocalPublisher)
    
    def test_get_publisher_invalid(self):
        """Test getting invalid publisher type."""
        with pytest.raises(ValueError, match="Unknown blog type"):
            get_publisher("invalid")
    
    def test_publish_creates_file(self, temp_blog_dir):
        """Test that publishing creates a file."""
        publisher = LocalPublisher()
        
        content = "# Test Digest\n\nContent here."
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        result_path = publisher.publish(content, title, config)
        
        assert Path(result_path).exists()
        assert Path(result_path).read_text() == content
    
    def test_publish_creates_markdown_file(self, temp_blog_dir):
        """Test that published file has .md extension."""
        publisher = LocalPublisher()
        
        content = "# Test Digest"
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        result_path = publisher.publish(content, title, config)
        
        assert result_path.endswith(".md")
    
    def test_publish_with_slug_prefix(self, temp_blog_dir):
        """Test publishing with a slug prefix."""
        publisher = LocalPublisher()
        
        content = "# Test Digest"
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        result_path = publisher.publish(content, title, config, slug_prefix="digests")
        
        # The slug prefix should be in the filename (with dash separator)
        assert "digests" in result_path
    
    def test_publish_creates_subdirectory(self, temp_blog_dir):
        """Test that subdirectories are created if needed."""
        publisher = LocalPublisher()
        
        content = "# Test Digest"
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        result_path = publisher.publish(content, title, config, slug_prefix="nested/path")
        
        # The path should include the nested directory structure
        assert "nested" in result_path
        assert Path(result_path).exists()
    
    def test_publish_content_preserved(self, temp_blog_dir):
        """Test that published content is preserved."""
        publisher = LocalPublisher()
        
        content = "# Test Digest\n\n* Bold text\n* List item"
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        result_path = publisher.publish(content, title, config)
        
        # Content should be in the file (may be prefixed with frontmatter)
        file_content = Path(result_path).read_text()
        assert "Test Digest" in file_content
        assert "Bold text" in file_content or "List item" in file_content
    
    def test_publish_with_jekyll_frontmatter(self, temp_blog_dir):
        """Test publishing with Jekyll YAML frontmatter."""
        publisher = LocalPublisher()
        
        content = "# Test Digest\n\nContent here."
        title = "Test Digest"
        config = {
            "path": temp_blog_dir,
            "frontmatter": True,
            "frontmatter_format": "yaml"
        }
        
        result_path = publisher.publish(content, title, config)
        
        written_content = Path(result_path).read_text()
        assert "---" in written_content
        assert "title:" in written_content
        assert "Test Digest" in written_content
    
    def test_publish_with_hugo_frontmatter(self, temp_blog_dir):
        """Test publishing with Hugo TOML frontmatter."""
        publisher = LocalPublisher()
        
        content = "# Test Digest"
        title = "Test Digest"
        config = {
            "path": temp_blog_dir,
            "frontmatter": True,
            "frontmatter_format": "toml"
        }
        
        result_path = publisher.publish(content, title, config)
        
        written_content = Path(result_path).read_text()
        assert "+++" in written_content
        assert "title" in written_content
    
    def test_publish_with_json_frontmatter(self, temp_blog_dir):
        """Test publishing with JSON frontmatter."""
        publisher = LocalPublisher()
        
        content = "# Test Digest"
        title = "Test Digest"
        config = {
            "path": temp_blog_dir,
            "frontmatter": True,
            "frontmatter_format": "json"
        }
        
        result_path = publisher.publish(content, title, config)
        
        written_content = Path(result_path).read_text()
        assert "<!--" in written_content
        assert "title" in written_content
        assert "-->" in written_content
    
    def test_publish_with_custom_frontmatter(self, temp_blog_dir):
        """Test publishing with custom frontmatter fields."""
        publisher = LocalPublisher()
        
        content = "# Test Digest"
        title = "Test Digest"
        config = {
            "path": temp_blog_dir,
            "frontmatter": True,
            "frontmatter_fields": {
                "tags": ["test", "digest"],
                "category": "updates"
            }
        }
        
        result_path = publisher.publish(content, title, config)
        
        written_content = Path(result_path).read_text()
        assert "tags:" in written_content or "tags =" in written_content or '"tags"' in written_content
        assert "test" in written_content
        assert "digest" in written_content
        assert "category" in written_content
        assert "updates" in written_content
    
    def test_publish_with_layout(self, temp_blog_dir):
        """Test publishing with a specified layout."""
        publisher = LocalPublisher()
        
        content = "# Test Digest"
        title = "Test Digest"
        config = {
            "path": temp_blog_dir,
            "frontmatter": True,
            "layout": "post"
        }
        
        result_path = publisher.publish(content, title, config)
        
        written_content = Path(result_path).read_text()
        assert "layout:" in written_content or "layout =" in written_content or '"layout"' in written_content
    
    def test_multiple_publishes_unique_filenames(self, temp_blog_dir):
        """Test that multiple publishes create unique filenames."""
        publisher = LocalPublisher()
        
        content = "# Test Digest"
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        path1 = publisher.publish(content, title, config)
        path2 = publisher.publish(content, title, config)
        
        # Filenames should be different due to timestamps
        assert path1 != path2
        assert Path(path1).exists()
        assert Path(path2).exists()


class TestPublisherIntegration:
    """Test integration scenarios for publishers."""
    
    def test_publish_digest_to_blog(self, temp_blog_dir):
        """Test publishing a complete digest to a blog."""
        publisher = LocalPublisher()
        
        digest_content = """# Digital Payments Weekly Digest

Week ending February 24, 2026

## Top Stories

### RBI releases new UPI guidelines
The Reserve Bank of India has announced new security guidelines for UPI transactions...

## All Articles

1. [UPI Security Update](https://example.com/article1) — New 2FA requirements
2. [PhonePe Market Share](https://example.com/article2) — Reaches 50% market share
"""
        
        config = {
            "path": temp_blog_dir,
            "frontmatter": True,
            "layout": "digest"
        }
        
        result_path = publisher.publish(
            digest_content,
            "Digital Payments Weekly Digest",
            config,
            slug_prefix="payments/digest"
        )
        
        assert result_path is not None
        assert Path(result_path).exists()
        # The path should contain elements from the slug_prefix
        assert "payments" in result_path or "digest" in result_path
    
    def test_publish_with_metadata(self, temp_blog_dir):
        """Test publishing with additional metadata."""
        publisher = LocalPublisher()
        
        content = "# Test"
        title = "Test Post"
        config = {
            "path": temp_blog_dir,
            "frontmatter": True
        }
        metadata = {
            "author": "nanobot",
            "tags": ["tech", "news"]
        }
        
        result_path = publisher.publish(content, title, config, metadata=metadata)
        
        written_content = Path(result_path).read_text()
        assert "author" in written_content
        assert "nanobot" in written_content
        assert "tech" in written_content
    
    def test_publish_creates_posts_directory(self, temp_blog_dir):
        """Test that _posts directory is created if needed."""
        publisher = LocalPublisher()
        
        # Give path to blog root, not posts dir
        blog_root = Path(temp_blog_dir)
        
        content = "# Test"
        title = "Test"
        config = {"path": str(blog_root), "posts_dir": "_posts"}
        
        result_path = publisher.publish(content, title, config)
        
        assert "_posts" in result_path
        assert Path(result_path).exists()
