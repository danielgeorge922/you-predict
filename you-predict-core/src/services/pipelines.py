"""Scheduled pipeline endpoints — triggered by Cloud Scheduler via HTTP POST.

Each endpoint is a thin wrapper that calls engine functions. The heavy logic
lives in engines/; these routes just wire settings, services, and engines.
"""

import logging

from fastapi import APIRouter, Response

from src.config.clients import get_bq_client, get_gcs_client, get_settings, get_youtube_client
from src.data_sources.bigquery import BigQueryService
from src.data_sources.gcs import GCSService
from src.data_sources.gcs_paths import GCSPathBuilder
from src.engines.discovery import DiscoveryEngine
from src.engines.features.registry import FEATURE_EXECUTION_ORDER
from src.engines.features.runner import FeatureRunner
from src.engines.transforms.channels import ChannelTransformer
from src.engines.transforms.videos import VideoTransformer
from src.scripts.subscribe_channels import subscribe
from src.utils.timestamps import utcnow

router = APIRouter(prefix="/pipelines", tags=["pipelines"])
logger = logging.getLogger(__name__)
_paths = GCSPathBuilder()


def _services() -> tuple[BigQueryService, GCSService]:
    settings = get_settings()
    bq = BigQueryService(get_bq_client(), settings.gcp_project_id, settings.bq_dataset)
    gcs = GCSService(get_gcs_client(), settings.gcs_raw_bucket)
    return bq, gcs


@router.post("/daily-channel-refresh")
async def daily_channel_refresh() -> Response:
    """Ingest all tracked channels → GCS → dim_channel + fact_channel_snapshot."""
    settings = get_settings()
    bq, gcs = _services()
    yt = get_youtube_client()
    now = utcnow()

    engine = DiscoveryEngine(bq, settings.monitoring_window_hours)
    channel_ids = engine.get_tracked_channel_ids()

    if not channel_ids:
        logger.info("daily-channel-refresh: no tracked channels")
        return Response(status_code=200)

    response = yt.fetch_channels_batched(channel_ids)
    raw_items = [item.model_dump(mode="json") for item in response.items]

    # GCS first — raw preserved before transform
    for item in raw_items:
        gcs.upload_json(_paths.channel_metadata(item["id"], now), item)

    results = ChannelTransformer(bq).transform(raw_items)
    logger.info("daily-channel-refresh: %s", results)
    return Response(status_code=200)


@router.post("/daily-video-refresh")
async def daily_video_refresh() -> Response:
    """Ingest active video metadata → GCS → dim_video."""
    settings = get_settings()
    bq, gcs = _services()
    yt = get_youtube_client()
    now = utcnow()

    engine = DiscoveryEngine(bq, settings.monitoring_window_hours)
    video_ids = engine.get_active_video_ids()

    if not video_ids:
        logger.info("daily-video-refresh: no active videos")
        return Response(status_code=200)

    response = yt.fetch_videos_batched(video_ids)
    raw_items = [item.model_dump(mode="json") for item in response.items]

    # GCS first
    for item in raw_items:
        gcs.upload_json(_paths.video_metadata(item["id"], now), item)

    result = VideoTransformer(bq).transform(raw_items)
    logger.info("daily-video-refresh: %s", result)
    return Response(status_code=200)


@router.post("/expire-monitoring")
async def expire_monitoring() -> Response:
    """Deactivate videos that have passed their monitoring window."""
    settings = get_settings()
    bq, _ = _services()
    expired = DiscoveryEngine(bq, settings.monitoring_window_hours).expire_monitoring()
    logger.info("expire-monitoring: deactivated %d videos", expired)
    return Response(status_code=200)


@router.post("/renew-subscriptions")
async def renew_subscriptions() -> Response:
    """Re-subscribe all tracked channels to PubSubHubbub.

    YouTube subscriptions expire after ~10 days. Run this every 4 days via
    Cloud Scheduler to keep all channels delivering webhook notifications.
    """
    settings = get_settings()
    if not settings.cloud_run_service_url:
        logger.error("renew-subscriptions: CLOUD_RUN_SERVICE_URL not set")
        return Response(status_code=500)

    callback_url = settings.cloud_run_service_url.rstrip("/") + "/webhook"
    bq, _ = _services()
    channel_ids = DiscoveryEngine(bq, settings.monitoring_window_hours).get_tracked_channel_ids()

    ok = sum(1 for cid in channel_ids if subscribe(cid, callback_url))
    logger.info("renew-subscriptions: %d/%d channels renewed", ok, len(channel_ids))
    return Response(status_code=200)


# ---------------------------------------------------------------------------
# Phase 7+ stubs — filled in when SQL + engine code is written
# ---------------------------------------------------------------------------


@router.post("/compute-features")
async def compute_features() -> Response:
    """Run all feature SQL MERGEs in dependency order."""
    bq, _ = _services()
    runner = FeatureRunner(bq)
    for name in FEATURE_EXECUTION_ORDER:
        runner.run(name)
    return Response(status_code=200)


@router.post("/compute-marts")
async def compute_marts() -> Response:
    """Run mart rollup queries (Phase 7)."""
    logger.info("compute-marts: not yet implemented")
    return Response(status_code=200)


@router.post("/quality-checks")
async def quality_checks() -> Response:
    """Run data quality checks (Phase 8)."""
    logger.info("quality-checks: not yet implemented")
    return Response(status_code=200)
