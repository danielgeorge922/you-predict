"""Tests for src.scripts.seed_categories — data integrity only."""

from src.scripts.seed_categories import YOUTUBE_CATEGORIES


class TestYoutubeCategories:
    def test_count(self):
        assert len(YOUTUBE_CATEGORIES) == 32

    def test_all_have_required_keys(self):
        for cat in YOUTUBE_CATEGORIES:
            assert "category_id" in cat
            assert "category_name" in cat

    def test_ids_are_unique(self):
        ids = [c["category_id"] for c in YOUTUBE_CATEGORIES]
        assert len(ids) == len(set(ids))

    def test_ids_are_integers(self):
        for cat in YOUTUBE_CATEGORIES:
            assert isinstance(cat["category_id"], int)

    def test_names_are_non_empty(self):
        for cat in YOUTUBE_CATEGORIES:
            assert isinstance(cat["category_name"], str)
            assert len(cat["category_name"]) > 0

    def test_common_categories_present(self):
        names = {c["category_name"] for c in YOUTUBE_CATEGORIES}
        assert "Music" in names
        assert "Gaming" in names
        assert "Entertainment" in names
        assert "Education" in names
