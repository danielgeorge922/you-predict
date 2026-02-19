"""Raw transcript text → dim_video_transcript.

Input: Transcript text string (already fetched and stored in GCS).
Output: dim_video_transcript (MERGE on video_id).

Called by: POST /tasks/transcript/{video_id}
"""

import logging
from datetime import datetime
from typing import Any

from src.data_sources.bigquery import BigQueryService
from src.engines.transforms.base import TransformResult
from src.models.dimensions import DimVideoTranscript
from src.utils.text import flesch_kincaid_grade, word_count

logger = logging.getLogger(__name__)


class TranscriptTransformer:
    """Transforms raw transcript text into dim_video_transcript."""

    def __init__(self, bq: BigQueryService) -> None:
        self._bq = bq

    def transform(
        self,
        transcript_text: str,
        video_id: str,
        gcs_uri: str,
        fetched_at: datetime,
    ) -> TransformResult:
        """Compute transcript features and merge into dim_video_transcript.

        Args:
            transcript_text: Full transcript as a single string.
            video_id: YouTube video ID.
            gcs_uri: GCS path where raw text is stored.
            fetched_at: When the transcript was fetched.
        """
        transcript = DimVideoTranscript(
            video_id=video_id,
            transcript_source="auto_generated",
            gcs_uri=gcs_uri,
            word_count=word_count(transcript_text),
            fetched_at=fetched_at,
            topic_keywords=[],  # TODO: TF-IDF or keyword extraction
            readability_score=flesch_kincaid_grade(transcript_text),
            has_profanity=None,  # TODO: profanity detection
        )
        row = transcript.model_dump(mode="json")

        affected = self._merge_transcript(row)
        return TransformResult("dim_video_transcript", affected, "merge")

    def _merge_transcript(self, row: dict[str, Any]) -> int:
        """MERGE dim_video_transcript on video_id."""
        sql = f"""
        MERGE `{{project}}.{{dataset}}.dim_video_transcript` T
        USING (
            SELECT
                '{row["video_id"]}' AS video_id,
                '{row.get("transcript_source", "auto_generated")}' AS transcript_source,
                '{row["gcs_uri"]}' AS gcs_uri,
                {row.get("word_count", 0)} AS word_count,
                TIMESTAMP '{row["fetched_at"]}' AS fetched_at,
                CAST(NULL AS ARRAY<STRING>) AS topic_keywords,
                {row.get("readability_score", 0.0)} AS readability_score,
                CAST(NULL AS BOOL) AS has_profanity
        ) S
        ON T.video_id = S.video_id
        WHEN MATCHED THEN UPDATE SET
            transcript_source = S.transcript_source,
            gcs_uri = S.gcs_uri,
            word_count = S.word_count,
            fetched_at = S.fetched_at,
            topic_keywords = S.topic_keywords,
            readability_score = S.readability_score,
            has_profanity = S.has_profanity
        WHEN NOT MATCHED THEN INSERT (
            video_id, transcript_source, gcs_uri, word_count,
            fetched_at, topic_keywords, readability_score, has_profanity
        ) VALUES (
            S.video_id, S.transcript_source, S.gcs_uri, S.word_count,
            S.fetched_at, S.topic_keywords, S.readability_score, S.has_profanity
        )
        """
        return self._bq.run_merge(sql)
