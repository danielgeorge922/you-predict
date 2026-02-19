"""Create the Cloud Tasks queue used for fan-out polling.

Cloud Tasks is a delayed HTTP request scheduler. When a new video is discovered,
we schedule 12+ future HTTP requests (snapshots at 1h, 2h, 4h, ... 72h after
publish). Cloud Tasks holds onto each request and fires it at the scheduled time,
retrying automatically if the server is unavailable.

Idempotent — skips the queue if it already exists.

Usage:
    python -m src.scripts.bootstrap_cloud_tasks
"""

import logging

from google.api_core.exceptions import AlreadyExists
from google.cloud import tasks_v2

from src.config.clients import get_settings, get_tasks_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def create_queue(
    client: tasks_v2.CloudTasksClient, project_id: str, location: str, queue_name: str
) -> None:
    """Create a Cloud Tasks queue if it doesn't exist."""
    parent = f"projects/{project_id}/locations/{location}"
    queue_path = f"{parent}/queues/{queue_name}"

    try:
        client.create_queue(parent=parent, queue=tasks_v2.Queue(name=queue_path))
        log.info("Created queue: %s", queue_path)
    except AlreadyExists:
        log.info("Queue already exists: %s", queue_path)


def main() -> None:
    settings = get_settings()
    log.info("Project: %s | Location: %s", settings.gcp_project_id, settings.cloud_tasks_location)

    create_queue(
        get_tasks_client(),
        settings.gcp_project_id,
        settings.cloud_tasks_location,
        settings.cloud_tasks_queue,
    )

    log.info("Cloud Tasks bootstrap complete.")


if __name__ == "__main__":
    main()
