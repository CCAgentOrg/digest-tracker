"""Tests for CLI commands."""

import pytest
import tempfile
import shutil
from click.testing import CliRunner
from pathlib import Path

from digest_tracker.cli import cli


@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_env():
    """Temporary environment for testing."""
    temp_dir = tempfile.mkdtemp()
    old_env = None
    try:
        # Set environment for temporary database
        import os
        old_env = os.environ.copy()
        os.environ["HOME"] = temp_dir
        
        yield temp_dir
    finally:
        # Restore environment
        if old_env:
            import os
            os.environ.clear()
            os.environ.update(old_env)
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestTopicCommands:
    """Test topic-related CLI commands."""
    
    def test_topic_add(self, runner, temp_env):
        """Test adding a new topic."""
        result = runner.invoke(cli, ["topic", "add", "test-topic", "--desc", "Test description"])
        
        assert result.exit_code == 0
        assert "Topic added" in result.output
        assert "test-topic" in result.output
    
    def test_topic_add_duplicate(self, runner, temp_env):
        """Test adding a duplicate topic."""
        # Add topic first
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        # Try to add again
        result = runner.invoke(cli, ["topic", "add", "test-topic"])
        
        assert result.exit_code != 0
    
    def test_topic_list_empty(self, runner, temp_env):
        """Test listing topics when empty."""
        result = runner.invoke(cli, ["topic", "list"])
        
        assert result.exit_code == 0
        assert "No topics found" in result.output
    
    def test_topic_list(self, runner, temp_env):
        """Test listing topics."""
        runner.invoke(cli, ["topic", "add", "topic1", "--desc", "First topic"])
        runner.invoke(cli, ["topic", "add", "topic2", "--desc", "Second topic"])
        
        result = runner.invoke(cli, ["topic", "list"])
        
        assert result.exit_code == 0
        assert "topic1" in result.output
        assert "topic2" in result.output
    
    def test_topic_remove(self, runner, temp_env):
        """Test removing a topic."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["topic", "remove", "test-topic"])
        
        assert result.exit_code == 0
        assert "Topic removed" in result.output
    
    def test_topic_remove_nonexistent(self, runner, temp_env):
        """Test removing a non-existent topic."""
        result = runner.invoke(cli, ["topic", "remove", "nonexistent"])
        
        assert result.exit_code == 0
        assert "Topic not found" in result.output
    
    def test_topic_info(self, runner, temp_env):
        """Test showing topic info."""
        runner.invoke(cli, ["topic", "add", "test-topic", "--desc", "Test description"])
        
        result = runner.invoke(cli, ["topic", "info", "test-topic"])
        
        assert result.exit_code == 0
        assert "test-topic" in result.output
        assert "Test description" in result.output
    
    def test_topic_info_nonexistent(self, runner, temp_env):
        """Test showing info for non-existent topic."""
        result = runner.invoke(cli, ["topic", "info", "nonexistent"])
        
        assert result.exit_code == 0
        assert "Topic not found" in result.output


class TestSourceCommands:
    """Test source-related CLI commands."""
    
    def test_source_add(self, runner, temp_env):
        """Test adding a source to a topic."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["source", "add", "test-topic", "https://example.com/feed.xml"])
        
        assert result.exit_code == 0
        assert "Source added" in result.output
        assert "https://example.com/feed.xml" in result.output
    
    def test_source_add_nonexistent_topic(self, runner, temp_env):
        """Test adding a source to non-existent topic."""
        result = runner.invoke(cli, ["source", "add", "nonexistent", "https://example.com/feed.xml"])
        
        assert result.exit_code == 0
        assert "Topic not found" in result.output
    
    def test_source_add_with_type(self, runner, temp_env):
        """Test adding a source with type specified."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(
            cli, 
            ["source", "add", "test-topic", "https://example.com/page", "--type", "web"]
        )
        
        assert result.exit_code == 0
        assert "Source added" in result.output
    
    def test_source_list(self, runner, temp_env):
        """Test listing sources for a topic."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        runner.invoke(cli, ["source", "add", "test-topic", "https://example.com/feed.xml"])
        
        result = runner.invoke(cli, ["source", "list", "test-topic"])
        
        assert result.exit_code == 0
        assert "https://example.com/feed.xml" in result.output
    
    def test_source_list_empty(self, runner, temp_env):
        """Test listing sources when topic has none."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["source", "list", "test-topic"])
        
        assert result.exit_code == 0
        assert "No sources found" in result.output
    
    def test_source_remove(self, runner, temp_env):
        """Test removing a source."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        # Add source and extract ID from output
        add_result = runner.invoke(cli, ["source", "add", "test-topic", "https://example.com/feed.xml"])
        source_id = add_result.output.split("ID: ")[1].strip()
        
        result = runner.invoke(cli, ["source", "remove", source_id])
        
        assert result.exit_code == 0
        assert "Source removed" in result.output


class TestBlogCommands:
    """Test blog-related CLI commands."""
    
    def test_blog_add(self, runner, temp_env):
        """Test adding a blog."""
        temp_blog_path = Path(temp_env) / "blog"
        
        result = runner.invoke(
            cli,
            ["blog", "add", "test-blog", "local", "--config", f'{{"path": "{temp_blog_path}"}}']
        )
        
        assert result.exit_code == 0
        assert "Blog added" in result.output
        assert "test-blog" in result.output
    
    def test_blog_list(self, runner, temp_env):
        """Test listing blogs."""
        temp_path = Path(temp_env) / "blog1"
        runner.invoke(cli, ["blog", "add", "blog1", "local", "--config", f'{{"path": "{temp_path}"}}'])
        
        temp_path2 = Path(temp_env) / "blog2"
        runner.invoke(cli, ["blog", "add", "blog2", "local", "--config", f'{{"path": "{temp_path2}"}}'])
        
        result = runner.invoke(cli, ["blog", "list"])
        
        assert result.exit_code == 0
        assert "blog1" in result.output
        assert "blog2" in result.output
    
    def test_blog_link(self, runner, temp_env):
        """Test linking a blog to a topic."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        temp_path = Path(temp_env) / "blog"
        runner.invoke(cli, ["blog", "add", "test-blog", "local", "--config", f'{{"path": "{temp_path}"}}'])
        
        result = runner.invoke(cli, ["blog", "link", "test-topic", "test-blog"])
        
        assert result.exit_code == 0
        assert "Linked blog" in result.output
    
    def test_blog_unlink(self, runner, temp_env):
        """Test unlinking a blog from a topic."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        temp_path = Path(temp_env) / "blog"
        runner.invoke(cli, ["blog", "add", "test-blog", "local", "--config", f'{{"path": "{temp_path}"}}'])
        runner.invoke(cli, ["blog", "link", "test-topic", "test-blog"])
        
        result = runner.invoke(cli, ["blog", "unlink", "test-topic"])
        
        assert result.exit_code == 0
        assert "Unlinked blog" in result.output


class TestDigestCommands:
    """Test digest-related CLI commands."""
    
    def test_generate_digest_no_articles(self, runner, temp_env):
        """Test generating digest when no articles exist."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["generate", "test-topic", "weekly"])
        
        assert result.exit_code == 0
        # Digest is generated but with 0 articles
        assert "article_count" in result.output.lower() or "Digest generated" in result.output or "0 articles" in result.output.lower()
    
    def test_history_empty(self, runner, temp_env):
        """Test digest history when no digests exist."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["history", "test-topic"])
        
        assert result.exit_code == 0
        assert "No digests found" in result.output
    
    def test_export_digest(self, runner, temp_env):
        """Test exporting a digest."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        # Generate a digest first
        generate_result = runner.invoke(cli, ["generate", "test-topic", "weekly"])
        
        # Extract digest ID from output
        if "ID:" in generate_result.output:
            digest_id = generate_result.output.split("ID: ")[1].split()[0]
            
            # Export
            temp_file = Path(temp_env) / "export.md"
            result = runner.invoke(
                cli, 
                ["export", digest_id, "--output", str(temp_file)]
            )
            
            assert result.exit_code == 0
            assert temp_file.exists()


class TestFetchCommands:
    """Test fetch-related CLI commands."""
    
    def test_fetch_no_sources(self, runner, temp_env):
        """Test fetching when topic has no sources."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["fetch", "test-topic"])
        
        assert result.exit_code == 0
        assert "No sources" in result.output
    
    def test_fetch_nonexistent_topic(self, runner, temp_env):
        """Test fetching for non-existent topic."""
        result = runner.invoke(cli, ["fetch", "nonexistent"])
        
        assert result.exit_code == 0
        assert "Topic not found" in result.output


class TestPublishCommands:
    """Test publish-related CLI commands."""
    
    def test_publish_nonexistent_digest(self, runner, temp_env):
        """Test publishing non-existent digest."""
        result = runner.invoke(cli, ["publish", "nonexistent-id"])
        
        assert result.exit_code == 0
        assert "Digest not found" in result.output
    
    def test_publish_dry_run(self, runner, temp_env):
        """Test publish dry-run mode."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        temp_path = Path(temp_env) / "blog"
        runner.invoke(cli, ["blog", "add", "test-blog", "local", "--config", f'{{"path": "{temp_path}"}}'])
        runner.invoke(cli, ["blog", "link", "test-topic", "test-blog"])
        
        # Generate digest
        generate_result = runner.invoke(cli, ["generate", "test-topic", "weekly"])
        
        if "ID:" in generate_result.output:
            digest_id = generate_result.output.split("ID: ")[1].split()[0]
            
            result = runner.invoke(
                cli, 
                ["publish", digest_id, "--dry-run"]
            )
            
            assert result.exit_code == 0
            assert "Would publish" in result.output
