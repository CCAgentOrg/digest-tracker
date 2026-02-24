# digest-tracker

Track topics, fetch news, and generate digests with Turso storage.

[![Documentation](https://img.shields.io/badge/docs-live-blue.svg)](https://ccagentorg.github.io/digest-tracker/)

## Features

- **Topic Management**: Create and manage topics to track
- **Multiple Source Types**: RSS feeds, web pages, and more
- **Incremental Fetching**: Only fetch new content since last run
- **Digest Generation**: Create daily, weekly, or monthly digests
- **Blog Publishing**: Publish digests to local blogs, Hugo, Jekyll, and more
- **Turso Integration**: Cloud SQLite storage with optional local fallback

## Installation

```bash
pip install digest-tracker
```

Or install from source:

```bash
git clone https://github.com/CCAgentOrg/digest-tracker.git
cd digest-tracker
pip install -e .
```

## Quick Start

```bash
# Set up Turso (optional - uses local SQLite by default)
export TURSO_DATABASE_URL="libsql://your-db.turso.io"
export TURSO_AUTH_TOKEN="your-token"

# Add a topic
digest topic add "digital-payments" --desc "UPI, fintech, and digital payment news"

# Add RSS sources
digest source add "digital-payments" "https://example.com/feed.xml" --type rss

# Fetch articles
digest fetch "digital-payments" --days 7

# Generate a digest
digest generate "digital-payments" "weekly"

# Set up a blog for publishing
digest blog add "my-blog" "local" --config '{"path": "./blog/_posts"}'
digest blog link "digital-payments" "my-blog" --slug-prefix "digests/"

# Publish the digest
digest publish <digest-id>
```

## Commands

### Topic Management

```bash
digest topic add <name> [--desc <description>]
digest topic list
digest topic remove <name>
digest topic info <name>
```

### Source Management

```bash
digest source add <topic> <url> [--type rss|web|youtube]
digest source list <topic>
digest source remove <source_id>
```

### Blog Management

```bash
digest blog add <name> <type> [--config <json>]
digest blog list
digest blog link <topic> <blog> [--category <tag>] [--slug-prefix <prefix>]
digest blog unlink <topic>
```

### Fetching & Digests

```bash
digest fetch <topic> [--days 7]
digest generate <topic> <daily|weekly|monthly> [--from <date>] [--to <date>]
digest history <topic> [--limit 10]
digest view <digest_id>
digest export <digest_id> [--format markdown] [--output <path>]
digest publish <digest_id> [--blog <name>] [--dry-run]
```

## Configuration

The CLI can be configured via environment variables or a config file:

```bash
# Environment variables
export TURSO_DATABASE_URL="libsql://..."
export TURSO_AUTH_TOKEN="..."
```

## Blog Types

| Type | Description | Config Example |
|------|-------------|----------------|
| `local` | Write to local directory | `{"path": "./blog/_posts"}` |
| `hugo` | Hugo site | `{"path": "./hugo", "content_dir": "content/posts", "frontmatter_format": "toml"}` |
| `jekyll` | Jekyll site | `{"path": "./jekyll", "posts_dir": "_posts"}` |

## Development

```bash
# Install development dependencies
pip install -e ".[test]"

# Run tests
pytest

# Run with coverage
pytest --cov=digest_tracker --cov-report=html
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
