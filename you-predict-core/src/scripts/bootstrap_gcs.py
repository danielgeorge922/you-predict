"""Create GCS buckets for raw data and ML model artifacts.

Idempotent — skips buckets that already exist.

Usage:
    python -m src.scripts.bootstrap_gcs
"""

import logging

from google.api_core.exceptions import Conflict
from google.cloud.storage import Client

from src.config.clients import get_gcs_client, get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def create_bucket(client: Client, bucket_name: str, location: str) -> None:
    """Create a GCS bucket if it doesn't exist."""
    try:
        bucket = client.create_bucket(bucket_name, location=location)
        log.info("Created bucket: %s", bucket.name)
    except Conflict:
        log.info("Bucket already exists: %s", bucket_name)


def main() -> None:
    settings = get_settings()
    gcs = get_gcs_client()

    log.info("Project: %s", settings.gcp_project_id)
    create_bucket(gcs, settings.gcs_raw_bucket, settings.gcp_region)
    create_bucket(gcs, settings.gcs_model_bucket, settings.gcp_region)

    log.info("GCS bootstrap complete.")


if __name__ == "__main__":
    main()
