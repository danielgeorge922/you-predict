"""Cloud Tasks target handlers — snapshot, comments, transcript.

These endpoints are POSTed to by Cloud Tasks when delayed tasks fire.
All handlers are idempotent: redelivery produces the same BQ state.

Critical ordering: GCS write ALWAYS happens before BQ transform.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request, Response

from src.config.clients import (
    get_bq_client,
    get_gcs_client,
    get_settings,
    get_youtube_client,
)
from src.data_sources.bigquery import BigQueryService
from src.data_sources.gcs import GCSService
from src.data_sources.gcs_paths import GCSPathBuilder
from src.engines.transforms.comments import CommentTransformer
from src.engines.transforms.snapshots import SnapshotTransformer
from src.engines.transforms.transcripts import TranscriptTransformer
from src.utils.timestamps import parse_iso, utcnow

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)
_paths = GCSPathBuilder()


def _bq_gcs() -> tuple[BigQueryService, GCSService]:
    settings = get_settings()
    bq = BigQueryService(get_bq_client(), settings.gcp_project_id, settings.bq_dataset)
    gcs = GCSService(get_gcs_client(), settings.gcs_raw_bucket)
    return bq, gcs


@router.post("/snapshot/{video_id}")
async def handle_snapshot(video_id: str, interval: int, request: Request) -> Response:
    """Fetch video statistics and write a fact_video_snapshot row.

    Query param: interval (int) — nominal hours since publish (e.g. 4).
    Body: {"video_id", "channel_id", "published_at", "interval_hours"}
    """
    body: dict[str, Any] = await request.json()
    channel_id: str = body["channel_id"]
    published_at: datetime = parse_iso(body["published_at"])
    captured_at = utcnow()

    yt = get_youtube_client()
    bq, gcs = _bq_gcs()

    response = yt.fetch_video_stats([video_id])
    if not response.items:
        logger.warning("No stats returned for video %s at interval %dh", video_id, interval)
        return Response(status_code=200)

    raw_item = response.items[0].model_dump(mode="json")

    # GCS first — raw data preserved before any processing
    gcs.upload_json(_paths.video_snapshot(video_id, captured_at), raw_item)

    result = SnapshotTransformer(bq).transform(
        raw_item=raw_item,
        video_id=video_id,
        channel_id=channel_id,
        interval_hours=interval,
        published_at=published_at,
        captured_at=captured_at,
    )
    logger.info("Snapshot %s@%dh: %s", video_id, interval, result)
    return Response(status_code=200)


@router.post("/comments/{video_id}")
async def handle_comments(video_id: str, request: Request) -> Response:
    """Fetch comment threads and write fact_comment rows.

    Body: {"video_id", "channel_id", "published_at"}
    """
    body: dict[str, Any] = await request.json()
    channel_id: str = body["channel_id"]
    pulled_at = utcnow()

    yt = get_youtube_client()
    bq, gcs = _bq_gcs()

    response = yt.fetch_comment_threads(video_id)
    raw_items = [t.model_dump(mode="json") for t in response.items]

    # GCS first
    gcs.upload_json(_paths.video_comments(video_id, pulled_at), raw_items)

    result = CommentTransformer(bq).transform(
        raw_items=raw_items,
        video_id=video_id,
        channel_id=channel_id,
        pulled_at=pulled_at,
    )
    logger.info("Comments %s: %s", video_id, result)
    return Response(status_code=200)


@router.post("/transcript/{video_id}")
async def handle_transcript(video_id: str, request: Request) -> Response:
    """Fetch transcript and write a dim_video_transcript row.

    Body: {"video_id", "channel_id", "published_at"}
    """
    fetched_at = utcnow()
    bq, gcs = _bq_gcs()
    yt = get_youtube_client()

    transcript_text = yt.fetch_transcript(video_id)
    if transcript_text is None:
        logger.info("No transcript available for %s", video_id)
        return Response(status_code=200)

    # GCS first
    gcs_uri = gcs.upload_text(_paths.video_transcript(video_id), transcript_text)

    result = TranscriptTransformer(bq).transform(
        transcript_text=transcript_text,
        video_id=video_id,
        gcs_uri=gcs_uri,
        fetched_at=fetched_at,
    )
    logger.info("Transcript %s: %s", video_id, result)
    return Response(status_code=200)
