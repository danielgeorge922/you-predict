"""Tests for src.utils.retry."""

import pytest

from src.utils.retry import retry


class TestRetrySync:
    def test_succeeds_first_try(self):
        call_count = 0

        @retry(max_retries=3, base_delay=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert succeed() == "ok"
        assert call_count == 1

    def test_retries_then_succeeds(self):
        call_count = 0

        @retry(max_retries=3, base_delay=0.01)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        assert fail_twice() == "ok"
        assert call_count == 3

    def test_exhausts_retries(self):
        @retry(max_retries=2, base_delay=0.01)
        def always_fail():
            raise ValueError("always")

        with pytest.raises(ValueError, match="always"):
            always_fail()

    def test_only_retries_specified_exceptions(self):
        call_count = 0

        @retry(max_retries=3, base_delay=0.01, retryable_exceptions=(TypeError,))
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            raise_value_error()
        assert call_count == 1


class TestRetryAsync:
    @pytest.mark.asyncio
    async def test_async_succeeds(self):
        call_count = 0

        @retry(max_retries=3, base_delay=0.01)
        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert await succeed() == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_retries_then_succeeds(self):
        call_count = 0

        @retry(max_retries=3, base_delay=0.01)
        async def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("not yet")
            return "ok"

        assert await fail_once() == "ok"
        assert call_count == 2
