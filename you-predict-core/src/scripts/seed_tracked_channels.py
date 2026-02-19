"""Seed the tracked_channels table with the channels we want to monitor.

Idempotent — uses MERGE on channel_id, so safe to re-run. Existing rows are
updated (is_active, notes) but their added_at timestamp is preserved.

To add a new channel: append it to TRACKED_CHANNELS below and re-run.
To stop tracking a channel: set is_active=False in BQ directly (or remove
the entry and re-run to set it inactive via the MERGE).

Usage:
    uv run python -m src.scripts.seed_tracked_channels
"""

import logging

from src.config.clients import get_bq_client, get_settings
from src.data_sources.bigquery import BigQueryService
from src.utils.timestamps import utcnow

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Edit this list to define which channels the system tracks.
# Format: (channel_id, notes)
# ---------------------------------------------------------------------------

TRACKED_CHANNELS: list[tuple[str, str]] = [
    ("UCOsFVEylgXEcnxAEt9E0c4Q", ""),
    ("UC7ZUmtySp0bx2lw_1VGw3Yg", ""),
    ("UCq6VFHwMzcMXbuKyG7SQYIg", ""),
    ("UCp-9VZEYKho8zI7IFmmlX3Q", ""),
    ("UCAuk798iHprjTtwlClkFxMA", ""),
    ("UCr-GHkKLpT9DgBXHQXI2WAw", "EpicRoberto"),  # me aka the goat
    ("UC9o13aexcHFSok7VYZ24EaQ", ""),
]


def main() -> None:
    if not TRACKED_CHANNELS:
        log.error(
            "TRACKED_CHANNELS list is empty. "
            "Add channel IDs to src/scripts/seed_tracked_channels.py before running."
        )
        return

    settings = get_settings()
    bq = BigQueryService(get_bq_client(), settings.gcp_project_id, settings.bq_dataset)
    now = utcnow().isoformat()

    values_sql = ",\n            ".join(
        f"('{channel_id}', TIMESTAMP '{now}', TRUE, '{notes}')"
        for channel_id, notes in TRACKED_CHANNELS
    )

    sql = f"""
    MERGE `{{project}}.{{dataset}}.tracked_channels` T
    USING (
        SELECT channel_id, added_at, is_active, notes
        FROM UNNEST([
            STRUCT<channel_id STRING, added_at TIMESTAMP, is_active BOOL, notes STRING>
            {values_sql}
        ])
    ) S
    ON T.channel_id = S.channel_id
    WHEN MATCHED THEN
        UPDATE SET is_active = S.is_active, notes = S.notes
    WHEN NOT MATCHED THEN
        INSERT (channel_id, added_at, is_active, notes)
        VALUES (S.channel_id, S.added_at, S.is_active, S.notes)
    """

    affected = bq.run_merge(sql)
    log.info(
        "Seeded %d channel(s) into tracked_channels (%d rows affected).",
        len(TRACKED_CHANNELS),
        affected,
    )


if __name__ == "__main__":
    main()
