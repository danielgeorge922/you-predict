"""Cloud Tasks fan-out — enqueue snapshot, comment, and transcript tasks.

Called once per newly discovered video (from the webhook handler).
Creates 15 tasks total:
  - 12 snapshot tasks at [1, 2, 4, 6, 8, 12, 16, 20, 24, 36, 48, 72] hours
  - 2  comment tasks  at [24, 72] hours
  - 1  transcript task at 24 hours

All tasks are HTTP POSTs to this same Cloud Run service, with scheduleTime
set to published_at + interval so they fire at the right moment.
"""

import json
import logging
from datetime import UTC, datetime

from google.api_core.exceptions import AlreadyExists
from google.cloud import tasks_v2  # pyright: ignore[reportAttributeAccessIssue]
from google.protobuf import timestamp_pb2

from src.config.clients import get_tasks_client
from src.config.constants import FANOUT_SCHEDULE
from src.config.settings import Settings
from src.utils.timestamps import add_hours

logger = logging.getLogger(__name__)


def enqueue_fanout(
    video_id: str,
    channel_id: str,
    published_at: datetime,
    settings: Settings,
) -> None:
    """Enqueue all fan-out tasks for a newly discovered video."""
    if not settings.cloud_run_service_url:
        logger.warning("cloud_run_service_url not set — skipping Cloud Tasks enqueue")
        return

    client = get_tasks_client()
    queue = (
        f"projects/{settings.gcp_project_id}"
        f"/locations/{settings.cloud_tasks_location}"
        f"/queues/{settings.cloud_tasks_queue}"
    )
    base_url = settings.cloud_run_service_url.rstrip("/")
    ok = 0
    failed = 0

    # Snapshot tasks
    for hours in FANOUT_SCHEDULE.snapshot_intervals_hours:
        success = _create_task(
            client=client,
            queue=queue,
            url=f"{base_url}/tasks/snapshot/{video_id}?interval={hours}",
            body={
                "video_id": video_id,
                "channel_id": channel_id,
                "interval_hours": hours,
                "published_at": published_at.isoformat(),
            },
            schedule_time=add_hours(published_at, hours),
            task_id=f"{video_id}-snapshot-{hours}h",
        )
        ok += success
        failed += 1 - success

    # Comment tasks
    for hours in FANOUT_SCHEDULE.comment_pull_hours:
        success = _create_task(
            client=client,
            queue=queue,
            url=f"{base_url}/tasks/comments/{video_id}",
            body={
                "video_id": video_id,
                "channel_id": channel_id,
                "published_at": published_at.isoformat(),
            },
            schedule_time=add_hours(published_at, hours),
            task_id=f"{video_id}-comments-{hours}h",
        )
        ok += success
        failed += 1 - success

    # Transcript task
    success = _create_task(
        client=client,
        queue=queue,
        url=f"{base_url}/tasks/transcript/{video_id}",
        body={
            "video_id": video_id,
            "channel_id": channel_id,
            "published_at": published_at.isoformat(),
        },
        schedule_time=add_hours(published_at, FANOUT_SCHEDULE.transcript_fetch_hours),
        task_id=f"{video_id}-transcript",
    )
    ok += success
    failed += 1 - success

    if failed:
        logger.error("video %s: %d/%d tasks failed to enqueue", video_id, failed, ok + failed)
    else:
        logger.info("Enqueued %d Cloud Tasks for video %s", ok, video_id)


def _create_task(
    client: tasks_v2.CloudTasksClient,
    queue: str,
    url: str,
    body: dict[str, object],
    schedule_time: datetime,
    task_id: str,
) -> int:
    """Create a single delayed HTTP Cloud Task. Returns 1 on success, 0 on failure.

    task_id is used as the Cloud Tasks task name for deduplication — Cloud Tasks
    rejects a second create_task call with the same name within ~1 hour.
    """
    ts = timestamp_pb2.Timestamp()
    ts.FromDatetime(schedule_time.astimezone(UTC))

    task = tasks_v2.Task(
        name=f"{queue}/tasks/{task_id}",
        http_request=tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=url,
            headers={"Content-Type": "application/json"},
            body=json.dumps(body).encode(),
        ),
        schedule_time=ts,
    )
    try:
        client.create_task(request={"parent": queue, "task": task})
        logger.debug("Queued task: %s at %s", url, schedule_time.isoformat())
        return 1
    except AlreadyExists:
        # Duplicate webhook delivery — task already queued, this is expected.
        logger.debug("Task already exists (duplicate fanout): %s", task_id)
        return 1
    except Exception as exc:
        logger.error("Failed to enqueue task %s: %s", url, exc)
        return 0
