"""Text analysis utilities for title/description feature extraction."""

import re
import string

POWER_WORDS = frozenset({
    "insane", "secret", "shocking", "unbelievable", "incredible", "amazing",
    "ultimate", "exposed", "revealed", "banned", "warning", "urgent",
    "breaking", "exclusive", "epic", "crazy", "huge", "massive",
    "destroyed", "ruined", "worst", "best", "perfect", "impossible",
    "never", "always", "finally", "gone wrong", "not clickbait",
})

# Regex for common emoji Unicode ranges
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # misc symbols
    "\U0001f680-\U0001f6ff"  # transport
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U00002702-\U000027b0"  # dingbats
    "\U000024c2-\U0001f251"  # enclosed chars
    "]+",
    flags=re.UNICODE,
)

_URL_PATTERN = re.compile(r"https?://\S+")
_BRACKET_PATTERN = re.compile(r"\[.*?\]|\(.*?\)")


def has_emoji(text: str) -> bool:
    """Check if text contains emoji characters."""
    return bool(_EMOJI_PATTERN.search(text))


def caps_ratio(text: str) -> float:
    """Return ratio of uppercase letters to total letters."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def has_number(text: str) -> bool:
    """Check if text contains any digit."""
    return any(c.isdigit() for c in text)


def has_question(text: str) -> bool:
    """Check if text contains a question mark."""
    return "?" in text


def has_brackets(text: str) -> bool:
    """Check for bracket patterns like [GONE WRONG] or (NOT CLICKBAIT)."""
    return bool(_BRACKET_PATTERN.search(text))


def power_word_count(text: str) -> int:
    """Count power/clickbait words in text."""
    lower = text.lower()
    return sum(1 for word in POWER_WORDS if word in lower)


def count_links(text: str) -> int:
    """Count URLs in text."""
    return len(_URL_PATTERN.findall(text))


def word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def flesch_kincaid_grade(text: str) -> float:
    """Approximate Flesch-Kincaid grade level.

    Simplified — counts sentences by punctuation, syllables by vowel groups.
    """
    words = text.split()
    if not words:
        return 0.0

    sentences = max(1, sum(1 for c in text if c in ".!?"))
    syllables = sum(_count_syllables(w) for w in words)
    word_ct = len(words)

    return 0.39 * (word_ct / sentences) + 11.8 * (syllables / word_ct) - 15.59


def _count_syllables(word: str) -> int:
    """Rough syllable count based on vowel groups."""
    word = word.lower().strip(string.punctuation)
    if not word:
        return 1
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)
