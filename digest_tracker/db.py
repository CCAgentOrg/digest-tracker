"""Database models and connection handling."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import libsql_client


class Database:
    def __init__(self, database_url: str, auth_token: Optional[str] = None):
        # Use local SQLite if URL is empty or "file:"
        if not database_url or database_url.startswith("file:"):
            # Use local SQLite
            db_path = database_url.replace("file:", "") if database_url else str(Path.home() / ".local" / "share" / "digest-tracker" / "digest.db")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self._use_local_sqlite = True
            self._local_conn = sqlite3.connect(db_path)
            self._local_conn.row_factory = sqlite3.Row
        else:
            # Use Turso/libsql
            self._use_local_sqlite = False
            self.client = libsql_client.create_client(database_url, auth_token=auth_token)
        
        self._setup_tables()
    
    def execute(self, sql: str, params: Optional[tuple] = None, fetch: bool = False) -> Any:
        if self._use_local_sqlite:
            cursor = self._local_conn.execute(sql, params or ())
            if fetch:
                return cursor.fetchall()
            self._local_conn.commit()
            return None
        else:
            result = self.client.execute(sql, params or ())
            if fetch:
                return result.rows
            return result
    
    def executemany(self, sql: str, params: list[tuple]) -> Any:
        if self._use_local_sqlite:
            self._local_conn.executemany(sql, params)
            self._local_conn.commit()
        else:
            # libsql-client doesn't have executemany, execute one by one
            for p in params:
                self.client.execute(sql, p)
        return None
    
    def fetchone(self, sql: str, params: Optional[tuple] = None) -> Optional[dict]:
        if self._use_local_sqlite:
            cursor = self._local_conn.execute(sql, params or ())
            row = cursor.fetchone()
            return dict(row) if row else None
        else:
            result = self.execute(sql, params, fetch=True)
            return result[0] if result else None
    
    def fetchall(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        if self._use_local_sqlite:
            cursor = self._local_conn.execute(sql, params or ())
            return [dict(row) for row in cursor.fetchall()]
        else:
            return self.execute(sql, params, fetch=True)
    
    def _setup_tables(self):
        """Create all tables if they don't exist."""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS topics (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                active INTEGER DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                topic_id TEXT NOT NULL,
                url TEXT NOT NULL,
                source_type TEXT NOT NULL,
                config TEXT,
                last_fetched_at TEXT,
                last_cursor TEXT,
                metadata TEXT,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                title TEXT,
                url TEXT UNIQUE,
                published_at TEXT,
                author TEXT,
                content TEXT,
                summary TEXT,
                metadata TEXT,
                fetched_at TEXT,
                FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS blogs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                blog_type TEXT NOT NULL,
                config TEXT,
                active INTEGER DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS topic_blogs (
                topic_id TEXT NOT NULL,
                blog_id TEXT NOT NULL,
                category TEXT,
                slug_prefix TEXT,
                PRIMARY KEY (topic_id, blog_id),
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
                FOREIGN KEY (blog_id) REFERENCES blogs(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS digests (
                id TEXT PRIMARY KEY,
                topic_id TEXT NOT NULL,
                frequency TEXT,
                period_start TEXT,
                period_end TEXT,
                content TEXT,
                summary TEXT,
                article_count INTEGER,
                published INTEGER DEFAULT 0,
                blog_id TEXT,
                published_url TEXT,
                created_at TEXT,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
                FOREIGN KEY (blog_id) REFERENCES blogs(id) ON DELETE SET NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS schedules (
                id TEXT PRIMARY KEY,
                topic_id TEXT NOT NULL,
                frequency TEXT NOT NULL,
                cron_expr TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
            """,
        ]
        
        for table_sql in tables:
            self.execute(table_sql)
    
    # JSON helpers
    def json_loads(self, value: Optional[str]) -> Any:
        return json.loads(value) if value else None
    
    def json_dumps(self, value: Any) -> Optional[str]:
        return json.dumps(value) if value else None


# Topic operations
def create_topic(db: Database, name: str, description: Optional[str] = None) -> str:
    from .utils import generate_id
    topic_id = generate_id(name)
    db.execute(
        "INSERT INTO topics (id, name, description) VALUES (?, ?, ?)",
        (topic_id, name, description)
    )
    return topic_id


def get_topic_by_name(db: Database, name: str) -> Optional[dict]:
    row = db.fetchone("SELECT * FROM topics WHERE name = ? AND active = 1", (name,))
    if row:
        return dict(row)
    return None


def list_topics(db: Database) -> list[dict]:
    rows = db.fetchall("SELECT * FROM topics WHERE active = 1 ORDER BY name")
    return [dict(row) for row in rows]


def delete_topic(db: Database, name: str) -> bool:
    row = db.fetchone("SELECT id FROM topics WHERE name = ?", (name,))
    if not row:
        return False
    db.execute("UPDATE topics SET active = 0 WHERE id = ?", (row["id"],))
    return True


# Source operations
def create_source(db: Database, topic_id: str, url: str, source_type: str, config: Optional[dict] = None) -> str:
    from .utils import generate_id
    source_id = generate_id(f"{topic_id}-{url}")
    db.execute(
        "INSERT INTO sources (id, topic_id, url, source_type, config) VALUES (?, ?, ?, ?, ?)",
        (source_id, topic_id, url, source_type, db.json_dumps(config))
    )
    return source_id


def get_sources_for_topic(db: Database, topic_name: str) -> list[dict]:
    topic = get_topic_by_name(db, topic_name)
    if not topic:
        return []
    
    rows = db.fetchall("SELECT * FROM sources WHERE topic_id = ?", (topic["id"],))
    sources = []
    for row in rows:
        d = dict(row)
        d["config"] = db.json_loads(d["config"])
        d["metadata"] = db.json_loads(d["metadata"])
        sources.append(d)
    return sources


def delete_source(db: Database, source_id: str) -> bool:
    if db._use_local_sqlite:
        cursor = db._local_conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        db._local_conn.commit()
        return cursor.rowcount > 0
    else:
        result = db.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        return result.rows_affected > 0


# Article operations
def save_articles(db: Database, articles: list[dict]) -> int:
    from .utils import generate_id, now_utc
    
    saved = 0
    for article in articles:
        try:
            article_id = generate_id(article["url"])
            db.execute(
                """INSERT INTO articles 
                   (id, source_id, title, url, published_at, author, content, summary, metadata, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    article_id,
                    article["source_id"],
                    article.get("title"),
                    article["url"],
                    article.get("published_at"),
                    article.get("author"),
                    article.get("content"),
                    article.get("summary"),
                    db.json_dumps(article.get("metadata")),
                    now_utc()
                )
            )
            saved += 1
        except Exception:
            # Duplicate URL, skip
            pass
    return saved


def get_articles_for_digest(db: Database, topic_id: str, since: Optional[datetime] = None) -> list[dict]:
    sql = """
        SELECT a.* FROM articles a
        JOIN sources s ON a.source_id = s.id
        WHERE s.topic_id = ?
    """
    params = [topic_id]
    
    if since:
        sql += " AND a.published_at >= ?"
        params.append(since.isoformat())
    
    sql += " ORDER BY a.published_at DESC"
    
    rows = db.fetchall(sql, tuple(params))
    articles = []
    for row in rows:
        d = dict(row)
        d["metadata"] = db.json_loads(d["metadata"])
        articles.append(d)
    return articles


# Blog operations
def create_blog(db: Database, name: str, blog_type: str, config: dict) -> str:
    from .utils import generate_id
    blog_id = generate_id(name)
    db.execute(
        "INSERT INTO blogs (id, name, blog_type, config) VALUES (?, ?, ?, ?)",
        (blog_id, name, blog_type, db.json_dumps(config))
    )
    return blog_id


def list_blogs(db: Database) -> list[dict]:
    rows = db.fetchall("SELECT * FROM blogs WHERE active = 1 ORDER BY name")
    blogs = []
    for row in rows:
        d = dict(row)
        d["config"] = db.json_loads(d["config"])
        blogs.append(d)
    return blogs


def get_blog_by_name(db: Database, name: str) -> Optional[dict]:
    row = db.fetchone("SELECT * FROM blogs WHERE name = ? AND active = 1", (name,))
    if row:
        d = dict(row)
        d["config"] = db.json_loads(d["config"])
        return d
    return None


def link_blog_to_topic(db: Database, topic_name: str, blog_name: str, category: Optional[str] = None, slug_prefix: Optional[str] = None) -> bool:
    topic = get_topic_by_name(db, topic_name)
    if not topic:
        return False
    
    blog = get_blog_by_name(db, blog_name)
    if not blog:
        return False
    
    try:
        db.execute(
            "INSERT INTO topic_blogs (topic_id, blog_id, category, slug_prefix) VALUES (?, ?, ?, ?)",
            (topic["id"], blog["id"], category, slug_prefix)
        )
        return True
    except Exception:
        return False


def get_blog_for_topic(db: Database, topic_name: str) -> Optional[dict]:
    topic = get_topic_by_name(db, topic_name)
    if not topic:
        return None
    
    row = db.fetchone(
        """SELECT b.* FROM blogs b
           JOIN topic_blogs tb ON b.id = tb.blog_id
           WHERE tb.topic_id = ?""",
        (topic["id"],)
    )
    if row:
        d = dict(row)
        d["config"] = db.json_loads(d["config"])
        return d
    return None


def unlink_blog_from_topic(db: Database, topic_name: str) -> bool:
    topic = get_topic_by_name(db, topic_name)
    if not topic:
        return False
    
    if db._use_local_sqlite:
        cursor = db._local_conn.execute("DELETE FROM topic_blogs WHERE topic_id = ?", (topic["id"],))
        db._local_conn.commit()
        return cursor.rowcount > 0
    else:
        result = db.execute("DELETE FROM topic_blogs WHERE topic_id = ?", (topic["id"],))
        return result.rows_affected > 0


# Digest operations
def create_digest(db: Database, topic_id: str, frequency: str, period_start: datetime, period_end: datetime, content: str, summary: str, article_count: int, blog_id: Optional[str] = None) -> str:
    from .utils import generate_id, now_utc
    digest_id = generate_id(f"{topic_id}-{frequency}-{period_end.date()}")
    db.execute(
        """INSERT INTO digests 
           (id, topic_id, frequency, period_start, period_end, content, summary, article_count, blog_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            digest_id,
            topic_id,
            frequency,
            period_start.isoformat(),
            period_end.isoformat(),
            content,
            summary,
            article_count,
            blog_id,
            now_utc()
        )
    )
    return digest_id


def get_digests_for_topic(db: Database, topic_name: str, limit: int = 10) -> list[dict]:
    topic = get_topic_by_name(db, topic_name)
    if not topic:
        return []
    
    rows = db.fetchall(
        "SELECT * FROM digests WHERE topic_id = ? ORDER BY created_at DESC LIMIT ?",
        (topic["id"], limit)
    )
    return [dict(row) for row in rows]


def get_digest_by_id(db: Database, digest_id: str) -> Optional[dict]:
    row = db.fetchone("SELECT * FROM digests WHERE id = ?", (digest_id,))
    return dict(row) if row else None


def mark_digest_published(db: Database, digest_id: str, published_url: str) -> bool:
    if db._use_local_sqlite:
        cursor = db._local_conn.execute(
            "UPDATE digests SET published = 1, published_url = ? WHERE id = ?",
            (published_url, digest_id)
        )
        db._local_conn.commit()
        return cursor.rowcount > 0
    else:
        # For libsql, we need to fetch first to check if it exists
        existing = db.fetchone("SELECT id FROM digests WHERE id = ?", (digest_id,))
        if not existing:
            return False
        db.execute(
            "UPDATE digests SET published = 1, published_url = ? WHERE id = ?",
            (published_url, digest_id)
        )
        return True


# Schedule operations
def create_schedule(db: Database, topic_id: str, frequency: str, cron_expr: str) -> str:
    from .utils import generate_id
    schedule_id = generate_id(f"{topic_id}-{frequency}")
    db.execute(
        "INSERT INTO schedules (id, topic_id, frequency, cron_expr) VALUES (?, ?, ?, ?)",
        (schedule_id, topic_id, frequency, cron_expr)
    )
    return schedule_id


def list_schedules(db: Database) -> list[dict]:
    rows = db.fetchall(
        """SELECT s.*, t.name as topic_name 
           FROM schedules s 
           JOIN topics t ON s.topic_id = t.id
           WHERE s.enabled = 1 ORDER BY t.name, s.frequency"""
    )
    return [dict(row) for row in rows]


def delete_schedule(db: Database, topic_name: str, frequency: str) -> bool:
    topic = get_topic_by_name(db, topic_name)
    if not topic:
        return False
    
    if db._use_local_sqlite:
        cursor = db._local_conn.execute(
            "DELETE FROM schedules WHERE topic_id = ? AND frequency = ?",
            (topic["id"], frequency)
        )
        db._local_conn.commit()
        return cursor.rowcount > 0
    else:
        result = db.execute(
            "DELETE FROM schedules WHERE topic_id = ? AND frequency = ?",
            (topic["id"], frequency)
        )
        return result.rows_affected > 0
