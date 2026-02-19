"""Seed dim_category with YouTube video categories.

Idempotent — deletes all existing rows and re-inserts the full list each run.
Source: YouTube Data API videoCategories.list (US region).

Usage:
    python -m src.scripts.seed_categories
"""

import logging

from src.config.clients import get_bq_client, get_settings
from src.data_sources.bigquery import BigQueryService

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# Full list of YouTube categories (US region, as of 2025).
# IDs are not sequential — YouTube skips some numbers.
YOUTUBE_CATEGORIES: list[dict[str, int | str]] = [
    {"category_id": 1, "category_name": "Film & Animation"},
    {"category_id": 2, "category_name": "Autos & Vehicles"},
    {"category_id": 10, "category_name": "Music"},
    {"category_id": 15, "category_name": "Pets & Animals"},
    {"category_id": 17, "category_name": "Sports"},
    {"category_id": 18, "category_name": "Short Movies"},
    {"category_id": 19, "category_name": "Travel & Events"},
    {"category_id": 20, "category_name": "Gaming"},
    {"category_id": 21, "category_name": "Videoblogging"},
    {"category_id": 22, "category_name": "People & Blogs"},
    {"category_id": 23, "category_name": "Comedy"},
    {"category_id": 24, "category_name": "Entertainment"},
    {"category_id": 25, "category_name": "News & Politics"},
    {"category_id": 26, "category_name": "Howto & Style"},
    {"category_id": 27, "category_name": "Education"},
    {"category_id": 28, "category_name": "Science & Technology"},
    {"category_id": 29, "category_name": "Nonprofits & Activism"},
    {"category_id": 30, "category_name": "Movies"},
    {"category_id": 31, "category_name": "Anime/Animation"},
    {"category_id": 32, "category_name": "Action/Adventure"},
    {"category_id": 33, "category_name": "Classics"},
    {"category_id": 34, "category_name": "Comedy"},
    {"category_id": 35, "category_name": "Documentary"},
    {"category_id": 36, "category_name": "Drama"},
    {"category_id": 37, "category_name": "Family"},
    {"category_id": 38, "category_name": "Foreign"},
    {"category_id": 39, "category_name": "Horror"},
    {"category_id": 40, "category_name": "Sci-Fi/Fantasy"},
    {"category_id": 41, "category_name": "Thriller"},
    {"category_id": 42, "category_name": "Shorts"},
    {"category_id": 43, "category_name": "Shows"},
    {"category_id": 44, "category_name": "Trailers"},
]


def main() -> None:
    settings = get_settings()
    bq = BigQueryService(get_bq_client(), settings.gcp_project_id, settings.bq_dataset)

    # Wipe and reload for clean idempotency
    table_ref = f"{settings.gcp_project_id}.{settings.bq_dataset}.dim_category"
    bq.run_query(f"DELETE FROM `{table_ref}` WHERE TRUE")
    log.info("Cleared dim_category")

    bq.append_rows("dim_category", YOUTUBE_CATEGORIES)
    log.info("Seeded %d categories into dim_category.", len(YOUTUBE_CATEGORIES))


if __name__ == "__main__":
    main()
