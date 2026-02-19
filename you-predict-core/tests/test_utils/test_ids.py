"""Tests for src.utils.ids."""

import uuid

from src.utils.ids import generate_id


class TestGenerateId:
    def test_returns_string(self):
        result = generate_id()
        assert isinstance(result, str)

    def test_is_valid_uuid(self):
        result = generate_id()
        parsed = uuid.UUID(result)
        assert parsed.version == 4

    def test_unique(self):
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100
