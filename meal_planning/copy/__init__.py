"""Copy/content loader for markdown-based copy."""

from pathlib import Path
from functools import lru_cache

_COPY_DIR = Path(__file__).parent


@lru_cache
def get_copy(name: str) -> str:
    """Load copy from markdown file. Cached after first read."""
    return (_COPY_DIR / f"{name}.md").read_text()
