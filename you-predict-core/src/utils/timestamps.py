"""ISO parsing, timezone handling, and age calculations."""

from datetime import UTC, datetime, timedelta


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


def parse_iso(raw: str) -> datetime:
    """Parse an ISO 8601 string into a timezone-aware UTC datetime.

    Handles YouTube's format: '2026-02-15T08:30:00Z' and variants.
    """
    cleaned = raw.replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def hours_since(start: datetime, end: datetime | None = None) -> float:
    """Return hours elapsed between start and end (default: now)."""
    end = end or utcnow()
    delta = end - start
    return delta.total_seconds() / 3600


def days_since(start: datetime, end: datetime | None = None) -> int:
    """Return whole days elapsed between start and end (default: now)."""
    end = end or utcnow()
    delta = end - start
    return delta.days


def add_hours(dt: datetime, hours: int) -> datetime:
    """Add hours to a datetime."""
    return dt + timedelta(hours=hours)


def to_date_key(dt: datetime) -> int:
    """Convert datetime to YYYYMMDD integer key for dim_date."""
    return int(dt.strftime("%Y%m%d"))


def parse_iso8601_duration(duration: str) -> int:
    """Parse ISO 8601 duration (e.g. 'PT1H2M30S') to total seconds.

    YouTube's contentDetails.duration uses this format.
    """
    if not duration.startswith("PT"):
        return 0

    rest = duration[2:]
    total = 0

    for unit, multiplier in [("H", 3600), ("M", 60), ("S", 1)]:
        if unit in rest:
            value, rest = rest.split(unit, 1)
            total += int(value) * multiplier

    return total
