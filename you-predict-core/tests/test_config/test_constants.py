"""Tests for src.config.constants."""

from src.config.constants import (
    FANOUT_SCHEDULE,
    DurationBucket,
    FanoutSchedule,
    SubscriberTier,
    ViralityLabel,
)


class TestFanoutSchedule:
    def test_default_snapshot_intervals(self):
        assert FANOUT_SCHEDULE.snapshot_intervals_hours == (
            1,
            2,
            3,
            4,
            6,
            8,
            10,
            12,
            14,
            16,
            18,
            20,
            22,
            24,
            36,
            48,
            72,
        )

    def test_default_comment_pull_hours(self):
        assert FANOUT_SCHEDULE.comment_pull_hours == (24, 72)

    def test_default_transcript_fetch_hours(self):
        assert FANOUT_SCHEDULE.transcript_fetch_hours == 24

    def test_interval_to_snapshot_type(self):
        assert FANOUT_SCHEDULE.interval_to_snapshot_type(1) == "1h"
        assert FANOUT_SCHEDULE.interval_to_snapshot_type(24) == "24h"
        assert FANOUT_SCHEDULE.interval_to_snapshot_type(72) == "72h"

    def test_frozen(self):
        schedule = FanoutSchedule()
        try:
            schedule.snapshot_intervals_hours = (1, 2)  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass


class TestSubscriberTier:
    def test_micro(self):
        assert SubscriberTier.from_count(0) == SubscriberTier.MICRO
        assert SubscriberTier.from_count(9_999) == SubscriberTier.MICRO

    def test_small(self):
        assert SubscriberTier.from_count(10_000) == SubscriberTier.SMALL
        assert SubscriberTier.from_count(99_999) == SubscriberTier.SMALL

    def test_medium(self):
        assert SubscriberTier.from_count(100_000) == SubscriberTier.MEDIUM
        assert SubscriberTier.from_count(999_999) == SubscriberTier.MEDIUM

    def test_large(self):
        assert SubscriberTier.from_count(1_000_000) == SubscriberTier.LARGE
        assert SubscriberTier.from_count(50_000_000) == SubscriberTier.LARGE

    def test_values_are_strings(self):
        assert str(SubscriberTier.MICRO) == "micro"


class TestDurationBucket:
    def test_short(self):
        assert DurationBucket.from_seconds(0) == DurationBucket.SHORT
        assert DurationBucket.from_seconds(59) == DurationBucket.SHORT

    def test_medium(self):
        assert DurationBucket.from_seconds(60) == DurationBucket.MEDIUM
        assert DurationBucket.from_seconds(599) == DurationBucket.MEDIUM

    def test_long(self):
        assert DurationBucket.from_seconds(600) == DurationBucket.LONG
        assert DurationBucket.from_seconds(1799) == DurationBucket.LONG

    def test_very_long(self):
        assert DurationBucket.from_seconds(1800) == DurationBucket.VERY_LONG
        assert DurationBucket.from_seconds(7200) == DurationBucket.VERY_LONG


class TestViralityLabel:
    def test_values_exist(self):
        assert ViralityLabel.VIRAL == "viral"
        assert ViralityLabel.ABOVE_AVG == "above_avg"
        assert ViralityLabel.NORMAL == "normal"
        assert ViralityLabel.BELOW_AVG == "below_avg"
