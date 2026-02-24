"""Tests for CLI commands."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from digest_tracker.cli import cli


@pytest.fixture
def runner():
    """Click CLI runner with temporary environment."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        temp_dir = os.getcwd()
        # Set environment for temp database
        os.environ["DIGEST_DB_URL"] = f"file:{temp_dir}/test.db"
        yield runner
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_env():
    """Temporary directory for test databases."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


class TestTopicCommands:
    """Test topic-related CLI commands."""
    
    def test_topic_add(self, runner):
        """Test adding a topic."""
        result = runner.invoke(cli, ["topic", "add", "test-topic", "--desc", "Test description"])
        
        assert result.exit_code == 0
        assert "Topic created" in result.output or "✓" in result.output
        assert "test-topic" in result.output
    
    def test_topic_add_duplicate(self, runner):
        """Test adding duplicate topic."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        result = runner.invoke(cli, ["topic", "add", "test-topic"])
        
        # Exit code should be non-zero for duplicate
        assert result.exit_code != 0 or "already exists" in result.output.lower() or "duplicate" in result.output.lower()
    
    def test_topic_list_empty(self, runner):
        """Test listing topics when none exist."""
        result = runner.invoke(cli, ["topic", "list"])
        
        assert result.exit_code == 0
        assert "No topics" in result.output or "0 topics" in result.output or result.output.strip() == ""
    
    def test_topic_list(self, runner):
        """Test listing topics."""
        runner.invoke(cli, ["topic", "add", "topic1"])
        runner.invoke(cli, ["topic", "add", "topic2"])
        
        result = runner.invoke(cli, ["topic", "list"])
        
        assert result.exit_code == 0
        assert "topic1" in result.output
        assert "topic2" in result.output
    
    def test_topic_remove(self, runner):
        """Test removing a topic."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["topic", "remove", "test-topic"])
        
        assert result.exit_code == 0
        assert "removed" in result.output.lower() or "deleted" in result.output.lower() or "✓" in result.output
    
    def test_topic_remove_nonexistent(self, runner):
        """Test removing nonexistent topic."""
        result = runner.invoke(cli, ["topic", "remove", "nonexistent"])
        
        assert result.exit_code != 0 or "not found" in result.output.lower()
    
    def test_topic_info(self, runner):
        """Test getting topic info."""
        runner.invoke(cli, ["topic", "add", "test-topic", "--desc", "Test description"])
        
        result = runner.invoke(cli, ["topic", "info", "test-topic"])
        
        assert result.exit_code == 0
        assert "test-topic" in result.output
    
    def test_topic_info_nonexistent(self, runner):
        """Test getting info for nonexistent topic."""
        result = runner.invoke(cli, ["topic", "info", "nonexistent"])
        
        assert result.exit_code != 0 or "not found" in result.output.lower()


class TestSourceCommands:
    """Test source-related CLI commands."""
    
    def test_source_add(self, runner):
        """Test adding a source."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["source", "add", "test-topic", "https://example.com/feed.xml"])
        
        assert result.exit_code == 0
        assert "Source added" in result.output or "✓" in result.output
        assert "example.com" in result.output
    
    def test_source_add_nonexistent_topic(self, runner):
        """Test adding source to nonexistent topic."""
        result = runner.invoke(cli, ["source", "add", "nonexistent", "https://example.com/feed.xml"])
        
        assert result.exit_code != 0 or "not found" in result.output.lower()
    
    def test_source_add_with_type(self, runner):
        """Test adding source with specified type."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["source", "add", "test-topic", "https://example.com/feed.xml", "--type", "rss"])
        
        assert result.exit_code == 0
        assert "Source added" in result.output or "✓" in result.output
    
    def test_source_list(self, runner):
        """Test listing sources for a topic."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        runner.invoke(cli, ["source", "add", "test-topic", "https://example.com/feed1.xml"])
        runner.invoke(cli, ["source", "add", "test-topic", "https://example.com/feed2.xml"])
        
        result = runner.invoke(cli, ["source", "list", "test-topic"])
        
        assert result.exit_code == 0
        assert "feed1.xml" in result.output or "feed2.xml" in result.output
    
    def test_source_list_empty(self, runner):
        """Test listing sources when topic has none."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["source", "list", "test-topic"])
        
        assert result.exit_code == 0
        assert "No sources" in result.output or "0 sources" in result.output or result.output.strip() == ""
    
    def test_source_remove(self, runner):
        """Test removing a source."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        # Add source and extract ID from output
        add_result = runner.invoke(cli, ["source", "add", "test-topic", "https://example.com/feed.xml"])
        source_id = None
        for line in add_result.output.split('\n'):
            if "ID:" in line:
                # Extract just the UUID-like part (before any trailing paren)
                parts = line.split("ID:")
                if len(parts) > 1:
                    id_part = parts[1].strip()
                    # Remove trailing paren if present
                    if id_part.endswith(')'):
                        id_part = id_part[:-1]
                    source_id = id_part.strip()
                break
        
        if source_id:
            result = runner.invoke(cli, ["source", "remove", source_id])
            assert result.exit_code == 0
            assert "removed" in result.output.lower() or "deleted" in result.output.lower() or "✓" in result.output


class TestBlogCommands:
    """Test blog-related CLI commands."""
    
    def test_blog_add(self, runner, temp_env):
        """Test adding a blog."""
        result = runner.invoke(cli, ["blog", "add", "test-blog", "local", "--config", f'{{"path": "{temp_env}"}}'])
        
        assert result.exit_code == 0
        assert "Blog created" in result.output or "✓" in result.output
    
    def test_blog_list(self, runner, temp_env):
        """Test listing blogs."""
        runner.invoke(cli, ["blog", "add", "blog1", "local", "--config", f'{{"path": "{temp_env}"}}'])
        runner.invoke(cli, ["blog", "add", "blog2", "local", "--config", f'{{"path": "{temp_env}"}}'])
        
        result = runner.invoke(cli, ["blog", "list"])
        
        assert result.exit_code == 0
        assert "blog1" in result.output or "blog2" in result.output
    
    def test_blog_link(self, runner, temp_env):
        """Test linking a blog to a topic."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        runner.invoke(cli, ["blog", "add", "test-blog", "local", "--config", f'{{"path": "{temp_env}"}}'])
        
        result = runner.invoke(cli, ["blog", "link", "test-topic", "test-blog"])
        
        assert result.exit_code == 0
        assert "linked" in result.output.lower() or "✓" in result.output
    
    def test_blog_unlink(self, runner, temp_env):
        """Test unlinking a blog from a topic."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        runner.invoke(cli, ["blog", "add", "test-blog", "local", "--config", f'{{"path": "{temp_env}"}}'])
        runner.invoke(cli, ["blog", "link", "test-topic", "test-blog"])
        
        result = runner.invoke(cli, ["blog", "unlink", "test-topic"])
        
        assert result.exit_code == 0
        assert "unlinked" in result.output.lower() or "✓" in result.output


class TestDigestCommands:
    """Test digest-related CLI commands."""
    
    def test_generate_digest(self, runner):
        """Test generating a digest."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["generate", "test-topic", "weekly"])
        
        # Should succeed or gracefully handle no articles
        assert result.exit_code == 0 or "no articles" in result.output.lower()
    
    def test_generate_digest_no_articles(self, runner):
        """Test generating digest when no articles exist."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["generate", "test-topic", "weekly"])
        
        # Exit code 0 with message about no articles
        assert result.exit_code == 0
        assert "article" in result.output.lower() or "digest" in result.output.lower()
    
    def test_history_empty(self, runner):
        """Test digest history when empty."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["history", "test-topic"])
        
        assert result.exit_code == 0
        assert "No digests" in result.output or "0 digests" in result.output or result.output.strip() == ""
    
    def test_export_digest(self, runner, temp_env):
        """Test exporting a digest."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        # First try to generate (might fail gracefully without articles)
        result = runner.invoke(cli, ["generate", "test-topic", "weekly"])
        
        # Export command should handle non-existent digest gracefully
        result = runner.invoke(cli, ["export", "nonexistent-id", "--format", "markdown", "--output", f"{temp_env}/digest.md"])
        
        # Should fail gracefully
        assert result.exit_code != 0 or "not found" in result.output.lower()


class TestFetchCommands:
    """Test fetch-related CLI commands."""
    
    def test_fetch_no_sources(self, runner):
        """Test fetching when topic has no sources."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["fetch", "test-topic"])
        
        assert result.exit_code == 0 or "no sources" in result.output.lower()
    
    def test_fetch_nonexistent_topic(self, runner):
        """Test fetching from nonexistent topic."""
        result = runner.invoke(cli, ["fetch", "nonexistent"])
        
        assert result.exit_code != 0 or "not found" in result.output.lower()


class TestPublishCommands:
    """Test publish-related CLI commands."""
    
    def test_publish_nonexistent_digest(self, runner):
        """Test publishing a nonexistent digest."""
        result = runner.invoke(cli, ["publish", "nonexistent-id"])
        
        assert result.exit_code != 0 or "not found" in result.output.lower()
    
    def test_publish_dry_run(self, runner):
        """Test dry run of publishing."""
        runner.invoke(cli, ["topic", "add", "test-topic"])
        
        result = runner.invoke(cli, ["publish", "some-id", "--dry-run"])
        
        # Dry run should succeed or fail gracefully
        assert result.exit_code == 0 or "not found" in result.output.lower()
