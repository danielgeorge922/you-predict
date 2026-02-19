"""Subscribe tracked channels to YouTube PubSubHubbub notifications.

YouTube will POST Atom XML to our webhook whenever a subscribed channel
uploads a new video. Subscriptions expire after ~10 days and must be renewed
(or YouTube renews them automatically if the hub.verify succeeds).

Usage:
    # Subscribe all active channels from the tracked_channels BQ table (default):
    python -m src.scripts.subscribe_channels

    # Override with explicit channel IDs:
    python -m src.scripts.subscribe_channels UCX6OQ3DkcsbYNE6H8uQQuVA UC...

Prerequisites:
    - CLOUD_RUN_SERVICE_URL must be set (e.g. https://your-service-xyz.run.app)
    - The Cloud Run service must be deployed and the /webhook endpoint reachable
    - YouTube will send a GET verification request to /webhook?hub.challenge=...
      before the subscription is confirmed (async verification)
    - tracked_channels table must be seeded (run seed_tracked_channels.py first)
"""

import logging
import sys
import urllib.parse
import urllib.request

from src.config.clients import get_bq_client, get_settings
from src.data_sources.bigquery import BigQueryService
from src.engines.discovery import DiscoveryEngine

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

_HUB_URL = "https://pubsubhubbub.appspot.com/subscribe"
_YT_FEED_URL = "https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"


def subscribe(channel_id: str, callback_url: str, *, unsubscribe: bool = False) -> bool:
    """Send a subscribe (or unsubscribe) request to the PubSubHubbub hub.

    Args:
        channel_id: YouTube channel ID (e.g. UCX6OQ3DkcsbYNE6H8uQQuVA).
        callback_url: Full URL of our webhook endpoint (e.g. https://.../webhook).
        unsubscribe: If True, send hub.mode=unsubscribe instead.

    Returns:
        True if the hub accepted the request (HTTP 202 Accepted), False otherwise.
    """
    topic = _YT_FEED_URL.format(channel_id=channel_id)
    mode = "unsubscribe" if unsubscribe else "subscribe"

    data = urllib.parse.urlencode(
        {
            "hub.callback": callback_url,
            "hub.topic": topic,
            "hub.mode": mode,
            "hub.verify": "async",
        }
    ).encode()

    req = urllib.request.Request(_HUB_URL, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
    except Exception as exc:
        log.error("channel=%s  %s failed: %s", channel_id, mode, exc)
        return False

    if status == 202:
        log.info("channel=%-30s  %s accepted (202)", channel_id, mode)
        return True

    log.warning("channel=%-30s  %s unexpected status %d", channel_id, mode, status)
    return False


def main() -> None:
    settings = get_settings()

    if not settings.cloud_run_service_url:
        log.error("CLOUD_RUN_SERVICE_URL is not set — cannot build callback URL")
        sys.exit(1)

    callback_url = settings.cloud_run_service_url.rstrip("/") + "/webhook"

    # Channel IDs from CLI args, or fall back to tracked_channels BQ table
    if len(sys.argv) > 1:
        channel_ids = [c.strip() for c in sys.argv[1:] if c.strip()]
    else:
        bq = BigQueryService(get_bq_client(), settings.gcp_project_id, settings.bq_dataset)
        engine = DiscoveryEngine(bq)
        channel_ids = engine.get_tracked_channel_ids()

    if not channel_ids:
        log.error(
            "No channel IDs found. Seed tracked_channels first: "
            "uv run python -m src.scripts.seed_tracked_channels"
        )
        sys.exit(1)

    log.info("Webhook callback URL: %s", callback_url)
    log.info("Subscribing %d channel(s) to PubSubHubbub...", len(channel_ids))

    ok = 0
    failed = 0
    for cid in channel_ids:
        if subscribe(cid, callback_url):
            ok += 1
        else:
            failed += 1

    log.info("")
    log.info("Done. %d accepted, %d failed.", ok, failed)
    log.info(
        "YouTube will verify each subscription asynchronously via GET /webhook?hub.challenge=..."
    )

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
