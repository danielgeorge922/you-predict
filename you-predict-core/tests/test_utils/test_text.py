"""Tests for src.utils.text."""

from src.utils.text import (
    caps_ratio,
    count_links,
    flesch_kincaid_grade,
    has_brackets,
    has_emoji,
    has_number,
    has_question,
    power_word_count,
    word_count,
)


class TestHasEmoji:
    def test_with_emoji(self):
        assert has_emoji("Hello 😀 World") is True

    def test_without_emoji(self):
        assert has_emoji("Hello World") is False

    def test_empty_string(self):
        assert has_emoji("") is False


class TestCapsRatio:
    def test_all_caps(self):
        assert caps_ratio("HELLO") == 1.0

    def test_no_caps(self):
        assert caps_ratio("hello") == 0.0

    def test_mixed(self):
        assert caps_ratio("Hello") == 0.2

    def test_no_letters(self):
        assert caps_ratio("123!@#") == 0.0

    def test_empty(self):
        assert caps_ratio("") == 0.0


class TestHasNumber:
    def test_with_number(self):
        assert has_number("Top 10 Tips") is True

    def test_without_number(self):
        assert has_number("Hello World") is False


class TestHasQuestion:
    def test_with_question(self):
        assert has_question("Is this real?") is True

    def test_without_question(self):
        assert has_question("This is real") is False


class TestHasBrackets:
    def test_square_brackets(self):
        assert has_brackets("[GONE WRONG]") is True

    def test_parentheses(self):
        assert has_brackets("(NOT CLICKBAIT)") is True

    def test_no_brackets(self):
        assert has_brackets("Just a normal title") is False


class TestPowerWordCount:
    def test_multiple_power_words(self):
        assert power_word_count("INSANE SECRET REVEALED") == 3

    def test_no_power_words(self):
        assert power_word_count("A regular title about cooking") == 0

    def test_case_insensitive(self):
        assert power_word_count("This is SHOCKING") >= 1


class TestCountLinks:
    def test_multiple_links(self):
        text = "Check https://example.com and http://other.com"
        assert count_links(text) == 2

    def test_no_links(self):
        assert count_links("No links here") == 0


class TestWordCount:
    def test_normal_sentence(self):
        assert word_count("Hello world foo bar") == 4

    def test_empty(self):
        assert word_count("") == 0


class TestFleschKincaid:
    def test_simple_text(self):
        grade = flesch_kincaid_grade("The cat sat on the mat. It was a good cat.")
        assert isinstance(grade, float)

    def test_empty_text(self):
        assert flesch_kincaid_grade("") == 0.0
