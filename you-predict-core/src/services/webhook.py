"""PubSubHubbub webhook handler.

GET  /webhook  — Subscription verification (echo hub.challenge).
POST /webhook  — New video notification (parse Atom XML, register, fanout).

YouTube always gets a 200 back, even for malformed payloads, to prevent
redelivery loops. Errors are logged rather than surfaced as HTTP errors.
"""

import logging
import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse

from src.config.clients import get_bq_client, get_settings
from src.data_sources.bigquery import BigQueryService
from src.engines.discovery import DiscoveryEngine
from src.services.fanout import enqueue_fanout
from src.utils.timestamps import parse_iso, utcnow

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)

_ATOM = "http://www.w3.org/2005/Atom"
_YT = "http://www.youtube.com/xml/schemas/2015"


@router.get("")
async def webhook_verify(request: Request) -> PlainTextResponse:
    """YouTube hub.challenge verification — echo the challenge back."""
    challenge = request.query_params.get("hub.challenge")
    if not challenge:
        raise HTTPException(status_code=400, detail="Missing hub.challenge")
    return PlainTextResponse(challenge)


@router.post("")
async def webhook_notify(request: Request) -> Response:
    """Handle a PubSubHubbub push notification from YouTube.

    Parses the Atom XML, registers the video in video_monitoring (idempotent),
    and enqueues all fan-out Cloud Tasks on first discovery.
    """
    body = await request.body()
    if not body:
        return Response(status_code=200)

    try:
        root = ET.fromstring(body.decode("utf-8"))
    except ET.ParseError as exc:
        logger.warning("Webhook XML parse error: %s", exc)
        return Response(status_code=200)

    entry = root.find(f"{{{_ATOM}}}entry")
    if entry is None:
        # Feed-level ping (subscription renewal) — nothing to process.
        return Response(status_code=200)

    video_id_el = entry.find(f"{{{_YT}}}videoId")
    channel_id_el = entry.find(f"{{{_YT}}}channelId")
    published_el = entry.find(f"{{{_ATOM}}}published")

    if video_id_el is None or channel_id_el is None:
        logger.warning("Webhook entry missing yt:videoId or yt:channelId")
        return Response(status_code=200)

    video_id = (video_id_el.text or "").strip()
    channel_id = (channel_id_el.text or "").strip()
    published_raw = (published_el.text or "").strip() if published_el is not None else ""

    if not video_id or not channel_id:
        logger.warning("Webhook entry has empty video_id or channel_id")
        return Response(status_code=200)

    published_at = parse_iso(published_raw) if published_raw else utcnow()

    settings = get_settings()
    bq = BigQueryService(get_bq_client(), settings.gcp_project_id, settings.bq_dataset)
    engine = DiscoveryEngine(bq, settings.monitoring_window_hours)

    if engine.is_video_registered(video_id):
        logger.info("Duplicate webhook for video %s — already registered, skipping", video_id)
        return Response(status_code=200)

    is_new = engine.register_video(video_id, channel_id, published_at)
    if not is_new:
        logger.info("Duplicate webhook for video %s — skipping fanout", video_id)
        return Response(status_code=200)

    enqueue_fanout(video_id, channel_id, published_at, settings)
    logger.info("Webhook OK: video=%s channel=%s fanout enqueued", video_id, channel_id)
    return Response(status_code=200)
