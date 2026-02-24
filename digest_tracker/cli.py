"""CLI for digest-tracker."""

import click
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import Config
from .db import (
    Database, create_topic, get_topic_by_name, list_topics, delete_topic,
    create_source, get_sources_for_topic, delete_source, save_articles,
    create_blog, list_blogs, get_blog_by_name, link_blog_to_topic,
    get_blog_for_topic, unlink_blog_from_topic,
    get_digests_for_topic, get_digest_by_id, mark_digest_published,
    list_schedules, delete_schedule
)
from .digest import DigestGenerator
from .fetchers import get_fetcher
from .publishers import get_publisher


def get_db() -> Database:
    """Get database connection."""
    config = Config.load()
    return Database(
        database_url=config.turso.database_url,
        auth_token=config.turso.auth_token
    )


# Topic commands
@click.group()
def cli():
    """Digest Tracker - Track topics, fetch news, and generate digests."""
    pass


@cli.group()
def topic():
    """Manage topics."""
    pass


@topic.command("add")
@click.argument("name")
@click.option("--desc", help="Topic description")
def add_topic(name: str, desc: str):
    """Add a new topic to track."""
    db = get_db()
    topic_id = create_topic(db, name, desc)
    click.echo(f"✓ Topic added: {name} (ID: {topic_id})")


@topic.command("list")
def list_topics_cmd():
    """List all topics."""
    db = get_db()
    topics = list_topics(db)
    
    if not topics:
        click.echo("No topics found.")
        return
    
    for t in topics:
        status = "✓" if t["active"] else "✗"
        click.echo(f"{status} {t['name']}" + (f" — {t['description']}" if t['description'] else ""))


@topic.command("remove")
@click.argument("name")
def remove_topic(name: str):
    """Remove a topic."""
    db = get_db()
    if delete_topic(db, name):
        click.echo(f"✓ Topic removed: {name}")
    else:
        click.echo(f"✗ Topic not found: {name}")


@topic.command("info")
@click.argument("name")
def topic_info(name: str):
    """Show topic details."""
    db = get_db()
    topic = get_topic_by_name(db, name)
    
    if not topic:
        click.echo(f"✗ Topic not found: {name}")
        return
    
    sources = get_sources_for_topic(db, name)
    blog = get_blog_for_topic(db, name)
    digests = get_digests_for_topic(db, name, limit=5)
    
    click.echo(f"Topic: {topic['name']}")
    if topic['description']:
        click.echo(f"Description: {topic['description']}")
    click.echo(f"\nSources: {len(sources)}")
    for s in sources:
        click.echo(f"  • {s['source_type']}: {s['url']}")
    click.echo(f"\nBlog: {blog['name'] if blog else 'None'}")
    click.echo(f"\nRecent digests: {len(digests)}")
    for d in digests:
        click.echo(f"  • {d['frequency']} — {d['period_start'][:10]}")


# Source commands
@cli.group()
def source():
    """Manage content sources."""
    pass


@source.command("add")
@click.argument("topic")
@click.argument("url")
@click.option("--type", "source_type", default="rss", help="Source type (rss, web, youtube)")
@click.option("--config", help="JSON config for source")
def add_source(topic: str, url: str, source_type: str, config: str):
    """Add a source to a topic."""
    import json
    
    db = get_db()
    topic_data = get_topic_by_name(db, topic)
    
    if not topic_data:
        click.echo(f"✗ Topic not found: {topic}")
        return
    
    config_data = json.loads(config) if config else None
    source_id = create_source(db, topic_data["id"], url, source_type, config_data)
    click.echo(f"✓ Source added: {url} (ID: {source_id})")


@source.command("list")
@click.argument("topic")
def list_sources(topic: str):
    """List sources for a topic."""
    db = get_db()
    sources = get_sources_for_topic(db, topic)
    
    if not sources:
        click.echo(f"No sources found for topic: {topic}")
        return
    
    click.echo(f"Sources for {topic}:")
    for s in sources:
        last_fetched = s['last_fetched_at'][:10] if s['last_fetched_at'] else "Never"
        click.echo(f"  • [{s['source_type']}] {s['url']}")
        click.echo(f"    Last fetched: {last_fetched}")


@source.command("remove")
@click.argument("source_id")
def remove_source_cmd(source_id: str):
    """Remove a source."""
    db = get_db()
    if delete_source(db, source_id):
        click.echo(f"✓ Source removed: {source_id}")
    else:
        click.echo(f"✗ Source not found: {source_id}")


# Blog commands
@cli.group()
def blog():
    """Manage blogs."""
    pass


@blog.command("add")
@click.argument("name")
@click.argument("blog_type")
@click.option("--config", help="JSON config for blog")
def add_blog(name: str, blog_type: str, config: str):
    """Add a blog."""
    import json
    
    db = get_db()
    config_data = json.loads(config) if config else {}
    blog_id = create_blog(db, name, blog_type, config_data)
    click.echo(f"✓ Blog added: {name} (type: {blog_type}, ID: {blog_id})")


@blog.command("list")
def list_blogs_cmd():
    """List all blogs."""
    db = get_db()
    blogs = list_blogs(db)
    
    if not blogs:
        click.echo("No blogs found.")
        return
    
    for b in blogs:
        click.echo(f"✓ {b['name']} ({b['blog_type']})")
        if b.get('config', {}).get('path'):
            click.echo(f"  Path: {b['config']['path']}")


@blog.command("link")
@click.argument("topic")
@click.argument("blog")
@click.option("--category", help="Blog category/tag")
@click.option("--slug-prefix", help="URL slug prefix")
def link_blog_cmd(topic: str, blog: str, category: str, slug_prefix: str):
    """Link a blog to a topic."""
    db = get_db()
    if link_blog_to_topic(db, topic, blog, category, slug_prefix):
        click.echo(f"✓ Linked blog '{blog}' to topic '{topic}'")
    else:
        click.echo(f"✗ Failed to link. Check topic and blog names.")


@blog.command("unlink")
@click.argument("topic")
def unlink_blog_cmd(topic: str):
    """Unlink blog from topic."""
    db = get_db()
    if unlink_blog_from_topic(db, topic):
        click.echo(f"✓ Unlinked blog from topic '{topic}'")
    else:
        click.echo(f"✗ Failed to unlink.")


# Fetch commands
@cli.command("fetch")
@click.argument("topic")
@click.option("--days", default=7, help="Fetch articles from last N days")
def fetch(topic: str, days: int):
    """Fetch articles for a topic."""
    db = get_db()
    topic_data = get_topic_by_name(db, topic)
    
    if not topic_data:
        click.echo(f"✗ Topic not found: {topic}")
        return
    
    sources = get_sources_for_topic(db, topic)
    
    if not sources:
        click.echo(f"No sources for topic: {topic}")
        return
    
    since = datetime.now(timezone.utc) - timedelta(days=days)
    total_articles = []
    
    for source in sources:
        click.echo(f"Fetching from {source['url']}...")
        
        try:
            fetcher = get_fetcher(source["source_type"])
            articles = fetcher.fetch(
                source["url"],
                since=since,
                config=source.get("config")
            )
            
            # Add source_id to articles
            for article in articles:
                article["source_id"] = source["id"]
            
            total_articles.extend(articles)
            click.echo(f"  Found {len(articles)} articles")
            
            # Update last_fetched_at
            db.execute(
                "UPDATE sources SET last_fetched_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), source["id"])
            )
            
        except Exception as e:
            click.echo(f"  Error: {e}")
    
    # Save articles
    if total_articles:
        saved = save_articles(db, total_articles)
        click.echo(f"\n✓ Saved {saved} new articles to database")
    else:
        click.echo("\nNo new articles found")


# Digest commands
@cli.command("generate")
@click.argument("topic")
@click.argument("frequency", default="weekly")
@click.option("--days", default=7, help="Number of days to include")
@click.option("--from", "from_date", help="Start date (ISO format)")
@click.option("--to", "to_date", help="End date (ISO format)")
def generate_digest(topic: str, frequency: str, days: int, from_date: str, to_date: str):
    """Generate a digest for a topic."""
    db = get_db()
    config = Config.load()
    
    since = None
    until = None
    
    if from_date:
        since = datetime.fromisoformat(from_date)
    if to_date:
        until = datetime.fromisoformat(to_date)
    
    generator = DigestGenerator(db, config.digests.model_dump())
    result = generator.generate(topic, frequency, days, since, until)
    
    if result:
        click.echo(f"\n✓ Digest generated!")
        click.echo(f"  ID: {result['digest_id']}")
        click.echo(f"  Period: {result['period']}")
        click.echo(f"  Articles: {result['article_count']}")
        click.echo(f"\n--- CONTENT ---\n")
        click.echo(result["content"])
    else:
        click.echo("Failed to generate digest")


@cli.command("history")
@click.argument("topic")
@click.option("--limit", default=10, help="Number of digests to show")
def history(topic: str, limit: int):
    """Show digest history for a topic."""
    db = get_db()
    digests = get_digests_for_topic(db, topic, limit)
    
    if not digests:
        click.echo(f"No digests found for topic: {topic}")
        return
    
    click.echo(f"Digest history for {topic}:")
    for d in digests:
        pub_status = "✓" if d["published"] else "✗"
        click.echo(f"  {pub_status} {d['frequency']} — {d['period_start'][:10]} to {d['period_end'][:10]} ({d['article_count']} articles)")
        click.echo(f"      ID: {d['id']}")


@cli.command("view")
@click.argument("digest_id")
def view_digest(digest_id: str):
    """View a digest."""
    db = get_db()
    digest = get_digest_by_id(db, digest_id)
    
    if not digest:
        click.echo(f"Digest not found: {digest_id}")
        return
    
    click.echo(f"Digest: {digest['id']}")
    click.echo(f"Frequency: {digest['frequency']}")
    click.echo(f"Period: {digest['period_start'][:10]} to {digest['period_end'][:10]}")
    click.echo(f"Articles: {digest['article_count']}")
    click.echo(f"\n--- CONTENT ---\n")
    click.echo(digest["content"])


@cli.command("export")
@click.argument("digest_id")
@click.option("--format", "fmt", default="markdown", help="Export format")
@click.option("--output", help="Output file path")
def export_digest(digest_id: str, fmt: str, output: str):
    """Export a digest."""
    db = get_db()
    digest = get_digest_by_id(db, digest_id)
    
    if not digest:
        click.echo(f"Digest not found: {digest_id}")
        return
    
    # For now, just export the content as-is
    # TODO: Add markdown formatting
    
    if output:
        Path(output).write_text(digest["content"])
        click.echo(f"✓ Exported to {output}")
    else:
        click.echo(digest["content"])


@cli.command("publish")
@click.argument("digest_id")
@click.option("--blog", help="Blog name (uses linked blog if not specified)")
@click.option("--dry-run", is_flag=True, help="Show what would be published")
def publish_digest(digest_id: str, blog: str, dry_run: bool):
    """Publish a digest."""
    db = get_db()
    digest = get_digest_by_id(db, digest_id)
    
    if not digest:
        click.echo(f"Digest not found: {digest_id}")
        return
    
    # Get blog
    from .db import get_topic_by_name, get_blog_by_name
    
    topic_data = db.fetchone("SELECT name FROM topics WHERE id = ?", (digest['topic_id'],))
    topic_name = topic_data['name'] if topic_data else "unknown"
    
    if blog:
        blog_data = get_blog_by_name(db, blog)
    else:
        blog_data = get_blog_for_topic(db, topic_name)
    
    if not blog_data:
        click.echo("No blog specified or linked to topic")
        return
    
    if dry_run:
        click.echo(f"Would publish digest {digest_id} to blog {blog_data['name']}")
        click.echo(f"Blog type: {blog_data['blog_type']}")
        return
    
    try:
        publisher = get_publisher(blog_data["blog_type"])
        
        # Get topic-blog link for slug_prefix
        link = db.fetchone(
            "SELECT * FROM topic_blogs WHERE topic_id = ? AND blog_id = ?",
            (digest['topic_id'], blog_data['id'])
        )
        slug_prefix = link['slug_prefix'] if link else None
        
        published_path = publisher.publish(
            digest["content"],
            f"{topic_name} {digest['frequency']} digest",
            blog_data["config"],
            slug_prefix=slug_prefix
        )
        
        # Mark as published
        mark_digest_published(db, digest_id, published_path)
        
        click.echo(f"✓ Published to: {published_path}")
        
    except Exception as e:
        click.echo(f"✗ Failed to publish: {e}")


if __name__ == "__main__":
    cli()
