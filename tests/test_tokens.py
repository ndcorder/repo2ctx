"""Tests for token counting."""

from repo2ctx.tokens import count_tokens


def test_openai_count_basic():
    result = count_tokens("hello world", "openai")
    assert result == 2


def test_openai_count_empty():
    result = count_tokens("", "openai")
    assert result == 0


def test_openai_count_long_text():
    text = "word " * 1000
    result = count_tokens(text, "openai")
    assert 900 < result < 1100  # ~1 token per word


def test_claude_count_basic():
    result = count_tokens("hello world", "claude")
    # 11 chars / 4 = 2.75, rounds down to 2
    assert result == 2


def test_claude_count_empty():
    result = count_tokens("", "claude")
    assert result == 1  # min 1


def test_claude_count_long_text():
    text = "x" * 400
    result = count_tokens(text, "claude")
    assert result == 100


def test_default_model_is_openai():
    assert count_tokens("hello") == count_tokens("hello", "openai")


def test_consistency_within_2_percent():
    """Token counts should be reasonably consistent across calls."""
    text = "def hello():\n    return 'world'\n" * 10
    count1 = count_tokens(text, "openai")
    count2 = count_tokens(text, "openai")
    assert count1 == count2
