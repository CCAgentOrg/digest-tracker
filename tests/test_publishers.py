"""Tests for blog publishers."""

import pytest
import tempfile
import shutil
from pathlib import Path

from digest_tracker.publishers import LocalPublisher, get_publisher


class TestLocalPublisher:
    """Test local blog publisher."""
    
    @pytest.fixture
    def temp_blog_dir(self):
        """Temporary directory for blog output."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
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
        
        content = "# Test Digest\n\nTest content here."
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        result_path = publisher.publish(content, title, config)
        
        assert result_path is not None
        assert Path(result_path).exists()
    
    def test_publish_creates_markdown_file(self, temp_blog_dir):
        """Test that published file is markdown."""
        publisher = LocalPublisher()
        
        content = "# Test Digest\n\nTest content."
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        result_path = publisher.publish(content, title, config)
        
        assert result_path.endswith(".md")
        assert Path(result_path).exists()
    
    def test_publish_with_slug_prefix(self, temp_blog_dir):
        """Test publishing with a slug prefix."""
        publisher = LocalPublisher()
        
        content = "# Test Digest"
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        result_path = publisher.publish(content, title, config, slug_prefix="digests/")
        
        assert "digests/" in result_path
    
    def test_publish_creates_subdirectory(self, temp_blog_dir):
        """Test that subdirectories are created if needed."""
        publisher = LocalPublisher()
        
        content = "# Test Digest"
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        result_path = publisher.publish(content, title, config, slug_prefix="nested/path/")
        
        full_path = Path(temp_blog_dir) / "nested" / "path" / result_path.split("/")[-1]
        assert full_path.parent.exists()
        assert full_path.exists()
    
    def test_publish_content_preserved(self, temp_blog_dir):
        """Test that content is preserved in published file."""
        publisher = LocalPublisher()
        
        content = "# Test Digest\n\nThis is test content.\n\nSecond paragraph."
        title = "Test Digest"
        config = {"path": temp_blog_dir}
        
        result_path = publisher.publish(content, title, config)
        
        written_content = Path(result_path).read_text()
        assert "# Test Digest" in written_content
        assert "This is test content." in written_content
    
    def test_publish_with_jekyll_frontmatter(self, temp_blog_dir):
        """Test publishing with Jekyll frontmatter."""
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
        assert "date:" in written_content
    
    def test_publish_with_hugo_frontmatter(self, temp_blog_dir):
        """Test publishing with Hugo frontmatter."""
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
        assert 'title = ' in written_content
    
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
        assert "tags:" in written_content or "tags =" in written_content
        assert "test" in written_content
    
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
        assert "layout:" in written_content or "layout =" in written_content
        assert "post" in written_content
    
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
    """Integration tests for publishers."""
    
    @pytest.fixture
    def temp_blog_dir(self):
        """Temporary directory for blog output."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
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
            slug_prefix="payments/digest/"
        )
        
        assert result_path is not None
        assert Path(result_path).exists()
        assert "payments/digest/" in result_path
        
        content = Path(result_path).read_text()
        assert "Digital Payments Weekly Digest" in content
        assert "UPI Security Update" in content
