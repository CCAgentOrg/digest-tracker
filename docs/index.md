# Digest Tracker

**Track topics, fetch news, and generate digests with Turso storage.**

Digest Tracker is a CLI tool that helps you stay on top of topics you care about. It fetches content from RSS feeds, websites, and other sources, stores everything in Turso (or local SQLite), and generates summarized digests that can be published to blogs.

## Features

- 📊 **Topic Tracking** - Organize topics you want to follow
- 📡 **Multiple Sources** - RSS feeds, web pages, YouTube (coming soon)
- 💾 **Turso Storage** - Cloud SQLite with automatic local fallback
- 📝 **Digest Generation** - Daily, weekly, or monthly summaries
- 📤 **Blog Publishing** - Export to Jekyll, Hugo, or any static site generator
- 🔄 **Incremental Fetching** - Only fetch new content since last run

## Installation

```bash
pip install digest-tracker
```

Or use the development version:

```bash
git clone https://github.com/CCAgentOrg/digest-tracker.git
cd digest-tracker
pip install -e .
```

## Quick Start

### 1. Create a Topic

```bash
digest topic add "digital-payments" --desc "UPI, fintech, and payment news"
```

### 2. Add Sources

```bash
digest source add "digital-payments" "https://www.thehindubusinessline.com/news/economy/feeder/default.rss"
digest source add "digital-payments" "https://mint.feedsportal.com/c/33833/f/640935/index.rss" --type rss
```

### 3. Fetch Articles

```bash
digest fetch "digital-payments" --days 7
```

### 4. Generate a Digest

```bash
digest generate "digital-payments" "weekly"
```

### 5. Publish to Blog

First, create a blog:

```bash
digest blog add "my-blog" "local" --config '{"path": "/path/to/blog", "posts_dir": "_posts"}'
```

Link it to your topic:

```bash
digest blog link "digital-payments" "my-blog" --category "payments" --slug-prefix "digests/"
```

Then publish:

```bash
digest publish <digest_id>
```

## Configuration

Digest Tracker looks for configuration in:

1. `~/.config/digest-tracker/config.yml`
2. Environment variables (`TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`)

### Example Config File

```yaml
turso:
  database_url: "libsql://your-db.turso.io"
  auth_token: "your-auth-token"

digests:
  default_frequency: "weekly"
  default_timezone: "Asia/Kolkata"
  max_articles_per_digest: 50
  whatsapp:
    brief: true
    show_urls: true
    emoji_header: true
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DIGEST_DB_URL` | Local SQLite path (for testing) |
| `TURSO_DATABASE_URL` | Turso database URL |
| `TURSO_AUTH_TOKEN` | Turso authentication token |

## CLI Commands

### Topics

```bash
digest topic add <name> [--desc <description>]
digest topic list
digest topic remove <name>
digest topic info <name>
```

### Sources

```bash
digest source add <topic> <url> [--type rss|web|youtube]
digest source list <topic>
digest source remove <source_id>
```

### Blogs

```bash
digest blog add <name> <type> [--config <json>]
digest blog list
digest blog link <topic> <blog> [--category <tag>] [--slug-prefix <prefix>]
digest blog unlink <topic>
```

### Fetching

```bash
digest fetch <topic> [--days 7]
```

### Digests

```bash
digest generate <topic> <daily|weekly|monthly> [--days 7] [--from <date>] [--to <date>]
digest history <topic> [--limit 10]
digest view <digest_id>
digest export <digest_id> [--format markdown] [--output <path>]
digest publish <digest_id> [--blog <name>] [--dry-run]
```

## Blog Types

### Local (Jekyll, Hugo)

For static site generators:

```bash
digest blog add "hugo-blog" "local" --config '{
  "path": "/path/to/hugo-site",
  "content_dir": "content/posts",
  "posts_dir": "_posts",
  "frontmatter": true,
  "frontmatter_format": "toml",
  "layout": "post"
}'
```

### Coming Soon

- **GitHub** - Push to GitHub Pages blogs
- **WordPress** - Publish via REST API

## Turso Setup

Digest Tracker uses Turso for cloud storage. Get started at https://turso.tech.

### Create a Database

```bash
turso db create digest-tracker
```

### Get Connection Details

```bash
turso db show digest-tracker --url
turso db tokens create digest-tracker
```

### Configure

```bash
export TURSO_DATABASE_URL="libsql://your-db.turso.io"
export TURSO_AUTH_TOKEN="your-token"
```

## Use Cases

### Weekly Newsletter

Track industry news and generate a weekly digest:

```bash
digest topic add "tech-news" --desc "Tech industry updates"
digest source add "tech-news" "https://techcrunch.com/feed/"
digest source add "tech-news" "https://www.theverge.com/rss/index.xml"

# Run weekly
digest fetch "tech-news" --days 7
digest generate "tech-news" "weekly"
digest publish <digest_id>
```

### Personal Research

Keep track of academic papers or blog posts:

```bash
digest topic add "llm-research" --desc "Large Language Model papers"
digest source add "llm-research" "https://arxiv.org/list/cs.AI/recent"
```

### Company Updates

Monitor competitor blogs or company news:

```bash
digest topic add "competitors" --desc "Company updates"
digest source add "competitors" "https://competitor.com/blog/feed.xml"
```

## Development

```bash
git clone https://github.com/CCAgentOrg/digest-tracker.git
cd digest-tracker
pip install -e ".[test]"

# Run tests
pytest

# Run linting
ruff check .
```

## License

MIT

## Contributing

Contributions welcome! See [CONTRIBUTING.md](https://github.com/CCAgentOrg/digest-tracker/blob/main/CONTRIBUTING.md) for details.
