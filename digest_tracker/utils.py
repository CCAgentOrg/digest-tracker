"""Utility functions."""

import secrets
from datetime import datetime, timezone
from hashlib import sha256


def generate_id(prefix: str = "", length: int = 12) -> str:
    """Generate a unique ID, optionally with a prefix."""
    if prefix:
        # Hash the prefix to get a consistent short string
        prefix_hash = sha256(prefix.encode()).hexdigest()[:8]
        random_part = secrets.token_hex(length)
        return f"{prefix_hash}-{random_part}"
    return secrets.token_hex(length)


def now_utc() -> str:
    """Get current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def parse_date(date_str: str) -> datetime:
    """Parse a date string to datetime."""
    from dateutil import parser
    return parser.parse(date_str)


def format_date(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%b %d, %Y %I:%M %p")


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')
