"""Run all bootstrap and seed scripts in the correct order.

Idempotent — every step is safe to re-run.

Usage:
    python -m src.scripts.bootstrap_all
"""

import logging

from src.scripts.bootstrap_bigquery import main as bootstrap_bigquery
from src.scripts.bootstrap_cloud_tasks import main as bootstrap_cloud_tasks
from src.scripts.bootstrap_gcs import main as bootstrap_gcs
from src.scripts.seed_categories import main as seed_categories
from src.scripts.seed_dates import main as seed_dates

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    log.info("=" * 60)
    log.info("STEP 1/5  GCS buckets")
    log.info("=" * 60)
    bootstrap_gcs()

    log.info("")
    log.info("=" * 60)
    log.info("STEP 2/5  BigQuery dataset + tables")
    log.info("=" * 60)
    bootstrap_bigquery()

    log.info("")
    log.info("=" * 60)
    log.info("STEP 3/5  Cloud Tasks queue")
    log.info("=" * 60)
    bootstrap_cloud_tasks()

    log.info("")
    log.info("=" * 60)
    log.info("STEP 4/5  Seed categories")
    log.info("=" * 60)
    seed_categories()

    log.info("")
    log.info("=" * 60)
    log.info("STEP 5/5  Seed dates")
    log.info("=" * 60)
    seed_dates()

    log.info("")
    log.info("Bootstrap complete. All infrastructure and seed data ready.")
    log.info("")
    log.info("Next step: seed your tracked channels, then subscribe to PubSubHubbub.")
    log.info("  1. Edit src/scripts/seed_tracked_channels.py — add your channel IDs")
    log.info("  2. uv run python -m src.scripts.seed_tracked_channels")
    log.info("  3. Deploy to Cloud Run, then:")
    log.info("  4. uv run python -m src.scripts.subscribe_channels")


if __name__ == "__main__":
    main()
