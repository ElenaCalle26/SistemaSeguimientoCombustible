"""LIKE/ILIKE helpers that bind values instead of concatenating SQL."""


def contains_pattern(value: str) -> str:
    """Escape LIKE wildcards so user input cannot widen a search."""
    escaped = (value or "").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
