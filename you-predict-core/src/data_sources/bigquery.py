"""BigQuery service — append, merge, query, table management."""

import logging
from typing import Any

from google.cloud import bigquery

logger = logging.getLogger(__name__)


class BigQueryService:
    """Handles all BigQuery operations for a given project/dataset."""

    def __init__(self, client: bigquery.Client, project_id: str, dataset: str) -> None:
        self._client = client
        self._project_id = project_id
        self._dataset = dataset

    def _table_ref(self, table_name: str) -> str:
        return f"{self._project_id}.{self._dataset}.{table_name}"

    def append_rows(self, table_name: str, rows: list[dict[str, Any]]) -> int:
        """Append rows via streaming insert. Returns count inserted."""
        if not rows:
            return 0

        errors = self._client.insert_rows_json(self._table_ref(table_name), rows)
        if errors:
            logger.error("Insert errors for %s: %s", table_name, errors)
            raise RuntimeError(f"BigQuery insert failed for {table_name}: {errors}")

        logger.info("Inserted %d rows into %s", len(rows), table_name)
        return len(rows)

    def run_query(self, sql: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        """Execute SQL with {project}/{dataset} placeholder substitution."""
        formatted = self._format_sql(sql, params)
        job = self._client.query(formatted)
        results = job.result()

        rows = [dict(row) for row in results]
        mb = (job.total_bytes_processed or 0) / 1e6
        logger.info("Query returned %d rows (%.1f MB)", len(rows), mb)
        return rows

    def run_merge(self, sql: str, params: dict[str, str] | None = None) -> int:
        """Execute a MERGE statement. Returns rows affected."""
        formatted = self._format_sql(sql, params)
        job = self._client.query(formatted)
        job.result()

        affected = job.num_dml_affected_rows or 0
        logger.info("MERGE affected %d rows", affected)
        return affected

    def table_exists(self, table_name: str) -> bool:
        try:
            self._client.get_table(self._table_ref(table_name))
            return True
        except Exception:
            return False

    def create_table(
        self,
        table_name: str,
        schema: list[bigquery.SchemaField],
        partition_field: str | None = None,
        clustering_fields: list[str] | None = None,
    ) -> None:
        """Create a table if it doesn't exist."""
        table = bigquery.Table(self._table_ref(table_name), schema=schema)

        if partition_field:
            table.time_partitioning = bigquery.TimePartitioning(field=partition_field)
        if clustering_fields:
            table.clustering_fields = clustering_fields

        self._client.create_table(table, exists_ok=True)
        logger.info("Table %s ready", self._table_ref(table_name))

    def _format_sql(self, sql: str, params: dict[str, str] | None = None) -> str:
        merged = {"project": self._project_id, "dataset": self._dataset}
        if params:
            merged.update(params)
        # Use explicit replace instead of .format() so that curly braces in
        # user data (channel descriptions, keywords, etc.) don't get treated
        # as format placeholders and raise KeyError.
        result = sql
        for key, value in merged.items():
            result = result.replace(f"{{{key}}}", value)
        return result
