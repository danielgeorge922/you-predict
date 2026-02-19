"""Tests for src.utils.timestamps."""

from datetime import UTC, datetime

from src.utils.timestamps import (
    add_hours,
    days_since,
    hours_since,
    parse_iso,
    parse_iso8601_duration,
    to_date_key,
    utcnow,
)


class TestUtcnow:
    def test_returns_aware_datetime(self):
        now = utcnow()
        assert now.tzinfo is not None

    def test_is_close_to_now(self):
        before = datetime.now(UTC)
        now = utcnow()
        after = datetime.now(UTC)
        assert before <= now <= after


class TestParseIso:
    def test_youtube_format_with_z(self):
        dt = parse_iso("2026-02-15T08:30:00Z")
        assert dt.year == 2026
        assert dt.month == 2
        assert dt.day == 15
        assert dt.hour == 8
        assert dt.minute == 30
        assert dt.tzinfo is not None

    def test_with_offset(self):
        dt = parse_iso("2026-02-15T08:30:00+00:00")
        assert dt.year == 2026
        assert dt.tzinfo is not None

    def test_naive_datetime_gets_utc(self):
        dt = parse_iso("2026-02-15T08:30:00")
        assert dt.tzinfo is not None


class TestHoursSince:
    def test_known_delta(self):
        start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        end = datetime(2026, 1, 1, 6, 30, tzinfo=UTC)
        assert hours_since(start, end) == 6.5

    def test_zero_delta(self):
        dt = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        assert hours_since(dt, dt) == 0.0


class TestDaysSince:
    def test_known_delta(self):
        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = datetime(2026, 1, 11, tzinfo=UTC)
        assert days_since(start, end) == 10

    def test_same_day(self):
        dt = datetime(2026, 6, 15, 10, 30, tzinfo=UTC)
        assert days_since(dt, dt) == 0


class TestAddHours:
    def test_add_positive(self):
        dt = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        result = add_hours(dt, 4)
        assert result == datetime(2026, 1, 1, 4, 0, tzinfo=UTC)

    def test_add_crosses_day(self):
        dt = datetime(2026, 1, 1, 23, 0, tzinfo=UTC)
        result = add_hours(dt, 2)
        assert result.day == 2
        assert result.hour == 1


class TestToDateKey:
    def test_conversion(self):
        dt = datetime(2026, 2, 15, 12, 0, tzinfo=UTC)
        assert to_date_key(dt) == 20260215

    def test_single_digit_month_day(self):
        dt = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)
        assert to_date_key(dt) == 20260105


class TestParseIso8601Duration:
    def test_hours_minutes_seconds(self):
        assert parse_iso8601_duration("PT1H2M30S") == 3750

    def test_minutes_only(self):
        assert parse_iso8601_duration("PT10M") == 600

    def test_seconds_only(self):
        assert parse_iso8601_duration("PT45S") == 45

    def test_hours_only(self):
        assert parse_iso8601_duration("PT2H") == 7200

    def test_invalid_prefix(self):
        assert parse_iso8601_duration("P1D") == 0

    def test_empty(self):
        assert parse_iso8601_duration("PT") == 0
