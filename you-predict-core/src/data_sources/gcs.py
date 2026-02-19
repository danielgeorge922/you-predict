"""Google Cloud Storage service — upload, read, list."""

import json
import logging
from typing import Any, cast

from google.cloud.storage import Client

logger = logging.getLogger(__name__)


class GCSService:
    """Handles all GCS raw layer I/O for a given bucket."""

    def __init__(self, client: Client, bucket_name: str) -> None:
        self._client = client
        self._bucket = client.bucket(bucket_name)
        self._bucket_name = bucket_name

    def upload_json(self, blob_path: str, data: Any) -> str:
        """Upload JSON-serializable data. Returns gs:// URI."""
        if hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")

        content = json.dumps(data, default=str)
        blob = self._bucket.blob(blob_path)
        blob.upload_from_string(content, content_type="application/json")

        uri = f"gs://{self._bucket_name}/{blob_path}"
        logger.info("Uploaded %d bytes to %s", len(content), uri)
        return uri

    def upload_text(self, blob_path: str, text: str) -> str:
        """Upload plain text. Returns gs:// URI."""
        blob = self._bucket.blob(blob_path)
        blob.upload_from_string(text, content_type="text/plain")

        uri = f"gs://{self._bucket_name}/{blob_path}"
        logger.info("Uploaded %d chars to %s", len(text), uri)
        return uri

    def read_json(self, blob_path: str) -> Any:
        """Read and parse a JSON blob."""
        blob = self._bucket.blob(blob_path)
        return json.loads(blob.download_as_text())

    def read_text(self, blob_path: str) -> str:
        """Read a text blob."""
        blob = self._bucket.blob(blob_path)
        return cast(str, blob.download_as_text())

    def list_blobs(self, prefix: str) -> list[str]:
        """List blob names under a prefix."""
        return [blob.name for blob in self._bucket.list_blobs(prefix=prefix)]
