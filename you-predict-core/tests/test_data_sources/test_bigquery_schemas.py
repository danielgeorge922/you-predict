"""Tests for src.data_sources.bigquery_schemas — schema registry integrity."""

from google.cloud.bigquery import SchemaField

from src.data_sources.bigquery_schemas import TABLE_REGISTRY


class TestTableRegistry:
    def test_has_all_expected_tables(self):
        expected = {
            "dim_channel", "dim_video", "dim_category", "dim_date",
            "dim_video_transcript", "video_monitoring", "tracked_channels",
            "fact_channel_snapshot", "fact_video_snapshot", "fact_comment",
            "ml_feature_video_performance", "ml_feature_video_content",
            "ml_feature_temporal", "ml_feature_channel",
            "ml_feature_comment_aggregates",
            "mart_video_summary", "mart_channel_daily",
            "ml_model_registry", "ml_prediction_log", "ml_experiment_log",
            "pipeline_run_log", "data_quality_results",
        }
        assert set(TABLE_REGISTRY.keys()) == expected

    def test_count(self):
        assert len(TABLE_REGISTRY) == 22

    def test_every_entry_has_valid_structure(self):
        for table_name, (schema, partition, clustering) in TABLE_REGISTRY.items():
            assert isinstance(schema, list), f"{table_name}: schema not a list"
            assert len(schema) > 0, f"{table_name}: schema is empty"
            assert all(isinstance(f, SchemaField) for f in schema), (
                f"{table_name}: schema contains non-SchemaField"
            )
            assert partition is None or isinstance(partition, str), (
                f"{table_name}: partition must be None or str"
            )
            assert clustering is None or isinstance(clustering, list), (
                f"{table_name}: clustering must be None or list"
            )

    def test_partition_fields_exist_in_schema(self):
        """If a table has a partition field, that field must exist in the schema."""
        for table_name, (schema, partition, _) in TABLE_REGISTRY.items():
            if partition is not None:
                field_names = {f.name for f in schema}
                assert partition in field_names, (
                    f"{table_name}: partition field '{partition}' not in schema"
                )

    def test_clustering_fields_exist_in_schema(self):
        """If a table has clustering fields, they must all exist in the schema."""
        for table_name, (schema, _, clustering) in TABLE_REGISTRY.items():
            if clustering is not None:
                field_names = {f.name for f in schema}
                for cf in clustering:
                    assert cf in field_names, (
                        f"{table_name}: clustering field '{cf}' not in schema"
                    )

    def test_every_schema_has_required_field(self):
        """Every table should have at least one REQUIRED field (the key)."""
        for table_name, (schema, _, _) in TABLE_REGISTRY.items():
            required = [f for f in schema if f.mode == "REQUIRED"]
            assert len(required) >= 1, (
                f"{table_name}: no REQUIRED fields found"
            )

    def test_fact_tables_are_partitioned(self):
        """All fact tables should be date-partitioned."""
        fact_tables = [t for t in TABLE_REGISTRY if t.startswith("fact_")]
        for table_name in fact_tables:
            _, partition, _ = TABLE_REGISTRY[table_name]
            assert partition is not None, (
                f"{table_name}: fact table should be partitioned"
            )
