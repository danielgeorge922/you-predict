"""Seed dim_date with a calendar dimension (2026-2028).

Idempotent — deletes all existing rows and re-inserts the full range each run.
Includes day-of-week, weekend flag, US holidays, and season.

Usage:
    python -m src.scripts.seed_dates
"""

import datetime
import logging
from typing import Any

from src.config.clients import get_bq_client, get_settings
from src.data_sources.bigquery import BigQueryService

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

START_DATE = datetime.date(2026, 1, 1)
END_DATE = datetime.date(2028, 12, 31)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Fixed-date US holidays. Floating holidays (Thanksgiving, etc.) are computed below.
FIXED_HOLIDAYS: dict[tuple[int, int], str] = {
    (1, 1): "New Year's Day",
    (7, 4): "Independence Day",
    (12, 25): "Christmas Day",
}


def _is_us_holiday(d: datetime.date) -> bool:
    """Check if a date is a major US holiday (fixed + floating)."""
    # Fixed holidays
    if (d.month, d.day) in FIXED_HOLIDAYS:
        return True

    # MLK Day: 3rd Monday of January
    if d.month == 1 and d.weekday() == 0 and 15 <= d.day <= 21:
        return True

    # Presidents' Day: 3rd Monday of February
    if d.month == 2 and d.weekday() == 0 and 15 <= d.day <= 21:
        return True

    # Memorial Day: last Monday of May
    if d.month == 5 and d.weekday() == 0 and d.day >= 25:
        return True

    # Labor Day: 1st Monday of September
    if d.month == 9 and d.weekday() == 0 and d.day <= 7:
        return True

    # Thanksgiving: 4th Thursday of November
    return d.month == 11 and d.weekday() == 3 and 22 <= d.day <= 28


def _season(d: datetime.date) -> str:
    """Northern hemisphere meteorological season."""
    if d.month in (3, 4, 5):
        return "spring"
    if d.month in (6, 7, 8):
        return "summer"
    if d.month in (9, 10, 11):
        return "fall"
    return "winter"


def _build_date_rows() -> list[dict[str, Any]]:
    """Generate one row per day from START_DATE to END_DATE."""
    rows: list[dict[str, Any]] = []
    current = START_DATE

    while current <= END_DATE:
        rows.append({
            "date_key": int(current.strftime("%Y%m%d")),
            "full_date": current.isoformat(),
            "year": current.year,
            "quarter": (current.month - 1) // 3 + 1,
            "month": current.month,
            "month_name": MONTH_NAMES[current.month],
            "week_of_year": current.isocalendar()[1],
            "day_of_month": current.day,
            "day_of_week": current.isoweekday(),
            "day_name": DAY_NAMES[current.weekday()],
            "is_weekend": current.weekday() >= 5,
            "is_us_holiday": _is_us_holiday(current),
            "season": _season(current),
        })
        current += datetime.timedelta(days=1)

    return rows


def main() -> None:
    settings = get_settings()
    bq = BigQueryService(get_bq_client(), settings.gcp_project_id, settings.bq_dataset)

    # Wipe and reload for clean idempotency
    table_ref = f"{settings.gcp_project_id}.{settings.bq_dataset}.dim_date"
    bq.run_query(f"DELETE FROM `{table_ref}` WHERE TRUE")
    log.info("Cleared dim_date")

    rows = _build_date_rows()
    bq.append_rows("dim_date", rows)
    log.info("Seeded %d date rows (%s to %s).", len(rows), START_DATE, END_DATE)


if __name__ == "__main__":
    main()
