"""Tests for TranscriptTransformer."""

from datetime import UTC, datetime

from src.engines.transforms.base import TransformResult
from src.engines.transforms.transcripts import TranscriptTransformer

_VIDEO_ID = "QJI0an6irrA"
_GCS_URI = "gs://you-predict-raw/video_transcripts/QJI0an6irrA/QJI0an6irrA_en.txt"
_FETCHED_AT = datetime(2026, 1, 8, 20, 0, 0, tzinfo=UTC)

# Actual transcript snippet from the notebook (QJI0an6irrA)
_REAL_TRANSCRIPT = (
    "In this video I gathered Kevin Hart Paris Hilton Howie Mandel "
    "and many more of my favorite celebrities Holy mackerel Enter our circle "
    "And I trapped them all in this red circle They had to survive inside "
    "the circle or lose a chance at one million dollars"
)

_SHORT_TRANSCRIPT = "Hello world this is a test"
_EMPTY_TRANSCRIPT = ""


class TestTranscriptTransform:

    def test_returns_dim_video_transcript_result(self, mock_bq):
        transformer = TranscriptTransformer(mock_bq)
        result = transformer.transform(
            transcript_text=_REAL_TRANSCRIPT,
            video_id=_VIDEO_ID,
            gcs_uri=_GCS_URI,
            fetched_at=_FETCHED_AT,
        )
        assert isinstance(result, TransformResult)
        assert result.table_name == "dim_video_transcript"
        assert result.write_method == "merge"

    def test_merge_called_once(self, mock_bq):
        transformer = TranscriptTransformer(mock_bq)
        transformer.transform(
            transcript_text=_REAL_TRANSCRIPT,
            video_id=_VIDEO_ID,
            gcs_uri=_GCS_URI,
            fetched_at=_FETCHED_AT,
        )
        mock_bq.run_merge.assert_called_once()

    def test_video_id_in_sql(self, mock_bq):
        transformer = TranscriptTransformer(mock_bq)
        transformer.transform(
            transcript_text=_REAL_TRANSCRIPT,
            video_id=_VIDEO_ID,
            gcs_uri=_GCS_URI,
            fetched_at=_FETCHED_AT,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert _VIDEO_ID in sql

    def test_gcs_uri_in_sql(self, mock_bq):
        transformer = TranscriptTransformer(mock_bq)
        transformer.transform(
            transcript_text=_REAL_TRANSCRIPT,
            video_id=_VIDEO_ID,
            gcs_uri=_GCS_URI,
            fetched_at=_FETCHED_AT,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert _GCS_URI in sql

    def test_word_count_nonzero_for_real_transcript(self, mock_bq):
        transformer = TranscriptTransformer(mock_bq)
        transformer.transform(
            transcript_text=_REAL_TRANSCRIPT,
            video_id=_VIDEO_ID,
            gcs_uri=_GCS_URI,
            fetched_at=_FETCHED_AT,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        # Real transcript has ~35 words — word_count should appear as a positive int
        # We check that it's not 0 by looking for "0 AS word_count" NOT being present
        assert "0 AS word_count" not in sql

    def test_word_count_for_short_transcript(self, mock_bq):
        transformer = TranscriptTransformer(mock_bq)
        transformer.transform(
            transcript_text=_SHORT_TRANSCRIPT,
            video_id=_VIDEO_ID,
            gcs_uri=_GCS_URI,
            fetched_at=_FETCHED_AT,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        # "Hello world this is a test" = 6 words
        assert "6 AS word_count" in sql

    def test_transcript_source_auto_generated(self, mock_bq):
        transformer = TranscriptTransformer(mock_bq)
        transformer.transform(
            transcript_text=_REAL_TRANSCRIPT,
            video_id=_VIDEO_ID,
            gcs_uri=_GCS_URI,
            fetched_at=_FETCHED_AT,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "auto_generated" in sql

    def test_readability_score_is_numeric(self, mock_bq):
        transformer = TranscriptTransformer(mock_bq)
        transformer.transform(
            transcript_text=_REAL_TRANSCRIPT,
            video_id=_VIDEO_ID,
            gcs_uri=_GCS_URI,
            fetched_at=_FETCHED_AT,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        # readability_score should be a float in the SQL — not NULL
        assert "NULL AS readability_score" not in sql

    def test_merge_on_video_id(self, mock_bq):
        transformer = TranscriptTransformer(mock_bq)
        transformer.transform(
            transcript_text=_REAL_TRANSCRIPT,
            video_id=_VIDEO_ID,
            gcs_uri=_GCS_URI,
            fetched_at=_FETCHED_AT,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "ON T.video_id = S.video_id" in sql
