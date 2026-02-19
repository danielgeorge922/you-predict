"""Create the BigQuery dataset and all tables.

Idempotent — dataset uses exists_ok, tables use exists_ok.
Reads TABLE_REGISTRY from bigquery_schemas.py as the single source of truth.

Usage:
    python -m src.scripts.bootstrap_bigquery
"""

import logging

from google.cloud import bigquery

from src.config.clients import get_bq_client, get_settings
from src.data_sources.bigquery import BigQueryService
from src.data_sources.bigquery_schemas import TABLE_REGISTRY

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def create_dataset(client: bigquery.Client, dataset_id: str, location: str) -> None:
    """Create the BigQuery dataset if it doesn't exist."""
    dataset_ref = bigquery.DatasetReference(client.project, dataset_id)
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = location

    client.create_dataset(dataset, exists_ok=True)
    log.info("Dataset ready: %s.%s", client.project, dataset_id)


def create_all_tables(bq: BigQueryService) -> None:
    """Create every table defined in TABLE_REGISTRY."""
    for table_name, (schema, partition_field, clustering_fields) in TABLE_REGISTRY.items():
        bq.create_table(table_name, schema, partition_field, clustering_fields)


def main() -> None:
    settings = get_settings()
    client = get_bq_client()

    log.info("Project: %s | Dataset: %s", settings.gcp_project_id, settings.bq_dataset)

    create_dataset(client, settings.bq_dataset, settings.gcp_region)

    bq = BigQueryService(client, settings.gcp_project_id, settings.bq_dataset)
    create_all_tables(bq)

    log.info("All %d tables ready.", len(TABLE_REGISTRY))


if __name__ == "__main__":
    main()
