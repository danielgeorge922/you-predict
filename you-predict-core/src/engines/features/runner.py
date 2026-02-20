"""Feature SQL runner — loads and executes feature MERGE statements."""

import logging
from pathlib import Path

from src.data_sources.bigquery import BigQueryService

logger = logging.getLogger(__name__)

# Path to src/sql/features/ relative to this file's location:
# engines/features/runner.py -> engines/ -> src/ -> src/sql/features/
_SQL_DIR = Path(__file__).parent.parent.parent / "sql" / "features"


class FeatureRunner:
    """Loads and executes feature SQL files against BigQuery.

    Each SQL file is a MERGE statement that uses {project} and {dataset}
    placeholders — substituted by BigQueryService._format_sql() internally.
    """

    def __init__(self, bq: BigQueryService) -> None:
        self._bq = bq

    def run(self, feature_name: str) -> int:
        """Execute the MERGE for a single feature table.

        Args:
            feature_name: Base name of the SQL file (e.g. "channel" runs
                          src/sql/features/channel.sql).

        Returns:
            Number of rows affected by the MERGE.
        """
        sql_path = _SQL_DIR / f"{feature_name}.sql"
        sql = sql_path.read_text(encoding="utf-8")

        logger.info("Running feature: %s", feature_name)
        affected = self._bq.run_merge(sql)
        logger.info("Feature %s complete: %d rows affected", feature_name, affected)
        return affected
