"""Enums, snapshot intervals, and business logic constants."""

from dataclasses import dataclass
from enum import StrEnum

# ---------------------------------------------------------------------------
# Schedules — grouped config for the fan-out polling system
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FanoutSchedule:
    """Defines when Cloud Tasks fire after a video is discovered."""

    snapshot_intervals_hours: tuple[int, ...] = (
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
    comment_pull_hours: tuple[int, ...] = (24, 72)
    transcript_fetch_hours: int = 24

    def interval_to_snapshot_type(self, hours: int) -> str:
        return f"{hours}h"


FANOUT_SCHEDULE = FanoutSchedule()


# ---------------------------------------------------------------------------
# Enums — status and classification labels
# ---------------------------------------------------------------------------


class InactiveReason(StrEnum):
    MONITORING_WINDOW_EXPIRED = "monitoring_window_expired"
    VIDEO_DELETED = "video_deleted"
    VIDEO_PRIVATED = "video_privated"
    MANUAL_STOP = "manual_stop"


class PipelineStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ModelStatus(StrEnum):
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class CheckType(StrEnum):
    FRESHNESS = "freshness"
    ROW_COUNT = "row_count"
    NULL_RATE = "null_rate"
    CUSTOM = "custom"


class ViralityLabel(StrEnum):
    VIRAL = "viral"
    ABOVE_AVG = "above_avg"
    NORMAL = "normal"
    BELOW_AVG = "below_avg"


# ---------------------------------------------------------------------------
# Classifiers — pure functions that bucket raw values into labels
# ---------------------------------------------------------------------------


class SubscriberTier(StrEnum):
    MICRO = "micro"  # <10K
    SMALL = "small"  # <100K
    MEDIUM = "medium"  # <1M
    LARGE = "large"  # 1M+

    @staticmethod
    def from_count(count: int) -> "SubscriberTier":
        if count < 10_000:
            return SubscriberTier.MICRO
        if count < 100_000:
            return SubscriberTier.SMALL
        if count < 1_000_000:
            return SubscriberTier.MEDIUM
        return SubscriberTier.LARGE


class DurationBucket(StrEnum):
    SHORT = "short"  # <60s (Shorts)
    MEDIUM = "medium"  # 1-10 min
    LONG = "long"  # 10-30 min
    VERY_LONG = "very_long"  # 30+ min

    @staticmethod
    def from_seconds(seconds: int) -> "DurationBucket":
        if seconds < 60:
            return DurationBucket.SHORT
        if seconds < 600:
            return DurationBucket.MEDIUM
        if seconds < 1800:
            return DurationBucket.LONG
        return DurationBucket.VERY_LONG
