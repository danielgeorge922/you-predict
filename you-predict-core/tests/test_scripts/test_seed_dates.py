"""Tests for src.scripts.seed_dates — pure logic only (no GCP calls)."""

import datetime

from src.scripts.seed_dates import _build_date_rows, _is_us_holiday, _season


class TestIsUsHoliday:
    def test_new_years_day(self):
        assert _is_us_holiday(datetime.date(2026, 1, 1)) is True

    def test_independence_day(self):
        assert _is_us_holiday(datetime.date(2026, 7, 4)) is True

    def test_christmas(self):
        assert _is_us_holiday(datetime.date(2026, 12, 25)) is True

    def test_regular_day(self):
        assert _is_us_holiday(datetime.date(2026, 3, 10)) is False

    def test_labor_day_2026(self):
        # First Monday of September 2026 is Sep 7
        assert _is_us_holiday(datetime.date(2026, 9, 7)) is True

    def test_thanksgiving_2026(self):
        # 4th Thursday of November 2026 is Nov 26
        assert _is_us_holiday(datetime.date(2026, 11, 26)) is True

    def test_memorial_day_2026(self):
        # Last Monday of May 2026 is May 25
        assert _is_us_holiday(datetime.date(2026, 5, 25)) is True


class TestSeason:
    def test_winter(self):
        assert _season(datetime.date(2026, 1, 15)) == "winter"
        assert _season(datetime.date(2026, 2, 15)) == "winter"
        assert _season(datetime.date(2026, 12, 15)) == "winter"

    def test_spring(self):
        assert _season(datetime.date(2026, 3, 15)) == "spring"
        assert _season(datetime.date(2026, 5, 15)) == "spring"

    def test_summer(self):
        assert _season(datetime.date(2026, 6, 15)) == "summer"
        assert _season(datetime.date(2026, 8, 15)) == "summer"

    def test_fall(self):
        assert _season(datetime.date(2026, 9, 15)) == "fall"
        assert _season(datetime.date(2026, 11, 15)) == "fall"


class TestBuildDateRows:
    def test_row_count(self):
        rows = _build_date_rows()
        # 2026: 365, 2027: 365, 2028: 366 (leap) = 1096
        assert len(rows) == 1096

    def test_first_row(self):
        rows = _build_date_rows()
        first = rows[0]
        assert first["date_key"] == 20260101
        assert first["full_date"] == "2026-01-01"
        assert first["year"] == 2026
        assert first["month"] == 1
        assert first["month_name"] == "January"
        assert first["is_us_holiday"] is True  # New Year's Day

    def test_last_row(self):
        rows = _build_date_rows()
        last = rows[-1]
        assert last["date_key"] == 20281231
        assert last["year"] == 2028

    def test_weekend_detection(self):
        rows = _build_date_rows()
        row_map = {r["date_key"]: r for r in rows}
        # Feb 15, 2026 is a Sunday
        assert row_map[20260215]["is_weekend"] is True
        assert row_map[20260215]["day_name"] == "Sunday"
        # Feb 16, 2026 is a Monday
        assert row_map[20260216]["is_weekend"] is False

    def test_quarter_calculation(self):
        rows = _build_date_rows()
        row_map = {r["date_key"]: r for r in rows}
        assert row_map[20260115]["quarter"] == 1
        assert row_map[20260415]["quarter"] == 2
        assert row_map[20260715]["quarter"] == 3
        assert row_map[20261015]["quarter"] == 4

    def test_all_rows_have_required_fields(self):
        rows = _build_date_rows()
        required = {
            "date_key", "full_date", "year", "quarter", "month",
            "month_name", "week_of_year", "day_of_month", "day_of_week",
            "day_name", "is_weekend", "is_us_holiday", "season",
        }
        for row in rows:
            assert set(row.keys()) == required
