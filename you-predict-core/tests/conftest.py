"""Shared fixtures for all tests."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Raw API fixture loaders
# ---------------------------------------------------------------------------


@pytest.fixture
def channel_item() -> dict:
    return json.loads((FIXTURES / "channel_mrbeast.json").read_text())


@pytest.fixture
def video_item_celebrities() -> dict:
    """Full metadata for QJI0an6irrA — 30 Celebrities Fight For $1,000,000!"""
    return json.loads((FIXTURES / "video_celebrities.json").read_text())


@pytest.fixture
def video_item_sky() -> dict:
    """Full metadata for ZFoNBxpXen4 — Survive 30 Days Trapped In The Sky."""
    return json.loads((FIXTURES / "video_sky.json").read_text())


@pytest.fixture
def video_stats_only() -> dict:
    """Statistics-only response for QJI0an6irrA (used by snapshot handler)."""
    return json.loads((FIXTURES / "video_stats_only.json").read_text())


@pytest.fixture
def comment_threads() -> list[dict]:
    return json.loads((FIXTURES / "comment_threads.json").read_text())


# ---------------------------------------------------------------------------
# Mock BigQueryService
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_bq() -> MagicMock:
    """BigQueryService mock — run_merge returns 1, run_query returns []."""
    bq = MagicMock()
    bq.run_merge.return_value = 1
    bq.run_query.return_value = []
    return bq


@pytest.fixture
def mock_bq_with_prev_snapshot() -> MagicMock:
    """BigQueryService mock pre-seeded with a previous snapshot row."""
    bq = MagicMock()
    bq.run_merge.return_value = 1
    bq.run_query.return_value = [
        {"view_count": 80_000_000, "like_count": 2_100_000, "comment_count": 90_000}
    ]
    return bq


@pytest.fixture
def mock_bq_with_prev_channel_snapshot() -> MagicMock:
    """BigQueryService mock pre-seeded with a previous channel snapshot row."""
    bq = MagicMock()
    bq.run_merge.return_value = 1
    bq.run_query.return_value = [
        {"view_count": 107_000_000_000, "subscriber_count": 460_000_000, "video_count": 935}
    ]
    return bq
