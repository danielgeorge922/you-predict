"""Shared helpers for all transforms.

Provides:
- safe_int(): Parse YouTube's string-typed stats ("12345") to int.
- best_thumbnail(): Pick the highest-res thumbnail URL from a ThumbnailSet.
- TransformResult: Simple dataclass reporting what a transform wrote
  (table name, row count, method used).

Every transform module imports from here. This file has no BigQuery
or GCS dependencies — it's pure utility code.
"""

from dataclasses import dataclass

from src.models.raw import ThumbnailSet


@dataclass
class TransformResult:
    """What a transform wrote to BigQuery."""

    table_name: str
    rows_written: int
    write_method: str  # "merge" or "append"


def safe_int(value: str | int | None) -> int | None:
    """Parse YouTube's string-typed stats to int.

    YouTube returns statistics as strings ("12345") and sometimes omits
    them entirely. This handles all cases without raising.

    Examples:
        safe_int("12345")  -> 12345
        safe_int(42)       -> 42
        safe_int(None)     -> None
        safe_int("")       -> None
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    value = str(value).strip()
    if not value:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def best_thumbnail(thumbnails: ThumbnailSet | None) -> str | None:
    """Pick the highest-resolution thumbnail URL.

    Priority: maxres > standard > high > medium > default.
    Returns None if no thumbnails available.
    """
    if thumbnails is None:
        return None

    for attr in ("maxres", "standard", "high", "medium", "default"):
        thumb = getattr(thumbnails, attr, None)
        if thumb is not None:
            url: str | None = thumb.url
            return url

    return None
