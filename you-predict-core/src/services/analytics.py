"""Analytics API endpoints — ad-hoc BigQuery reads for the dashboard."""

import logging
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.config.clients import get_bq_client, get_settings
from src.data_sources.bigquery import BigQueryService

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


def _bq() -> BigQueryService:
    settings = get_settings()
    return BigQueryService(get_bq_client(), settings.gcp_project_id, settings.bq_dataset)


# ---------------------------------------------------------------------------
# GET /analytics/channels
# Returns all tracked channels joined with their latest ML feature row.
# Used by: TopChannelsTable
# ---------------------------------------------------------------------------
_CHANNELS_SQL = """
SELECT
  c.channel_id,
  c.channel_name,
  COALESCE(c.thumbnail_url, '') AS thumbnail_url,
  COALESCE(c.subscriber_count, 0) AS subscriber_count,
  COALESCE(c.view_count, 0) AS view_count,
  COALESCE(c.video_count, 0) AS video_count,
  COALESCE(f.subscriber_growth_rate_30d, 0.0) AS subscriber_growth_rate_30d,
  COALESCE(f.avg_views_per_video_30d, 0.0) AS avg_views_per_video_30d,
  COALESCE(f.avg_engagement_rate_30d, 0.0) AS avg_engagement_rate_30d,
  COALESCE(f.channel_momentum_score, 0.0) AS channel_momentum_score
FROM `{project}.{dataset}.dim_channel` c
LEFT JOIN (
  SELECT *
  FROM `{project}.{dataset}.ml_feature_channel`
  WHERE computed_date = (
    SELECT MAX(computed_date) FROM `{project}.{dataset}.ml_feature_channel`
  )
) f ON c.channel_id = f.channel_id
ORDER BY f.channel_momentum_score DESC NULLS LAST
"""


@router.get("/channels")
async def get_channels() -> JSONResponse:
    """All tracked channels with latest feature metrics."""
    try:
        rows = _bq().run_query(_CHANNELS_SQL)
        return JSONResponse(content={"data": rows})
    except Exception as exc:
        logger.exception("Failed to query channels: %s", exc)
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ---------------------------------------------------------------------------
# GET /analytics/channel-movers
# Returns latest-day snapshot deltas for all channels, sorted by |views_delta|.
# Used by: BiggestMoversTable
# ---------------------------------------------------------------------------
_MOVERS_SQL = """
SELECT
  c.channel_id,
  c.channel_name,
  COALESCE(c.thumbnail_url, '') AS thumbnail_url,
  s.views_delta,
  s.subs_delta,
  s.snapshot_date
FROM `{project}.{dataset}.fact_channel_snapshot` s
JOIN `{project}.{dataset}.dim_channel` c ON s.channel_id = c.channel_id
WHERE s.snapshot_date = (
  SELECT MAX(snapshot_date) FROM `{project}.{dataset}.fact_channel_snapshot`
)
ORDER BY ABS(s.views_delta) DESC NULLS LAST
"""


@router.get("/channel-movers")
async def get_channel_movers() -> JSONResponse:
    """Latest-day channel snapshot deltas (biggest movers first)."""
    try:
        rows = _bq().run_query(_MOVERS_SQL)
        return JSONResponse(content={"data": rows})
    except Exception as exc:
        logger.exception("Failed to query channel movers: %s", exc)
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ---------------------------------------------------------------------------
# GET /analytics/summary?days=7
# Returns aggregated stat-card values for the given look-back window.
# Used by: StatCards
# ---------------------------------------------------------------------------
_SNAPSHOT_SUMMARY_SQL = """
SELECT
  COALESCE(SUM(views_delta), 0) AS total_views_delta,
  COALESCE(SUM(subs_delta), 0) AS total_subs_delta
FROM `{project}.{dataset}.fact_channel_snapshot`
WHERE snapshot_date = (
  SELECT MAX(snapshot_date) FROM `{project}.{dataset}.fact_channel_snapshot`
)
"""

_VIDEOS_PUBLISHED_SQL = """
SELECT COUNT(*) AS video_count
FROM `{project}.{dataset}.dim_video`
WHERE DATE(published_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
"""

_AVG_TOXICITY_SQL = """
SELECT ROUND(AVG(avg_toxicity) * 100, 1) AS avg_toxicity_pct
FROM (
  SELECT f.avg_toxicity
  FROM `{project}.{dataset}.ml_feature_comment_aggregates` f
  JOIN `{project}.{dataset}.video_monitoring` m ON f.video_id = m.video_id
  WHERE m.is_active = TRUE
    AND f.computed_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
)
"""


@router.get("/summary")
async def get_summary(days: int = Query(default=7, ge=1, le=90)) -> JSONResponse:
    """Aggregated stat-card metrics for the given look-back window (days)."""
    bq = _bq()
    days_str = str(days)

    result: dict[str, Any] = {
        "total_views_delta": None,
        "total_subs_delta": None,
        "videos_published": None,
        "avg_toxicity_pct": None,
    }

    try:
        snap_rows = bq.run_query(_SNAPSHOT_SUMMARY_SQL)
        if snap_rows:
            result["total_views_delta"] = snap_rows[0].get("total_views_delta")
            result["total_subs_delta"] = snap_rows[0].get("total_subs_delta")
    except Exception as exc:
        logger.warning("Snapshot summary query failed: %s", exc)

    try:
        vid_rows = bq.run_query(_VIDEOS_PUBLISHED_SQL, params={"days": days_str})
        if vid_rows:
            result["videos_published"] = vid_rows[0].get("video_count")
    except Exception as exc:
        logger.warning("Videos published query failed: %s", exc)

    try:
        tox_rows = bq.run_query(_AVG_TOXICITY_SQL, params={"days": days_str})
        if tox_rows:
            result["avg_toxicity_pct"] = tox_rows[0].get("avg_toxicity_pct")
    except Exception as exc:
        logger.warning("Avg toxicity query failed: %s", exc)

    return JSONResponse(content=result)
