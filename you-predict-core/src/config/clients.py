"""GCP client factories. Cached so each client is created once per process."""

import functools
from typing import TYPE_CHECKING

from google.cloud import bigquery, storage, tasks_v2

from src.config.settings import Settings

if TYPE_CHECKING:
    from src.data_sources.youtube.client import YouTubeClient


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


@functools.lru_cache(maxsize=1)
def get_bq_client() -> bigquery.Client:
    return bigquery.Client(project=get_settings().gcp_project_id)


@functools.lru_cache(maxsize=1)
def get_gcs_client() -> storage.Client:
    return storage.Client(project=get_settings().gcp_project_id)


@functools.lru_cache(maxsize=1)
def get_tasks_client() -> tasks_v2.CloudTasksClient:
    return tasks_v2.CloudTasksClient()


@functools.lru_cache(maxsize=1)
def get_youtube_client() -> "YouTubeClient":
    from src.data_sources.youtube.client import YouTubeClient

    return YouTubeClient(api_key=get_settings().youtube_api_key)
