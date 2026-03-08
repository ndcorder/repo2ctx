"""Token counting strategies for different LLM providers."""

from __future__ import annotations

import functools

import tiktoken


def count_tokens(text: str, model: str = "openai") -> int:
    """Count tokens in text using the specified model's tokenizer.

    Args:
        text: The text to count tokens for.
        model: Either "openai" (uses tiktoken cl100k_base) or "claude" (char-based estimate).

    Returns:
        Estimated token count.
    """
    if model == "claude":
        return _count_claude_tokens(text)
    return _count_openai_tokens(text)


@functools.cache
def _get_encoding():
    return tiktoken.get_encoding("cl100k_base")


def _count_openai_tokens(text: str) -> int:
    return len(_get_encoding().encode(text))


def _count_claude_tokens(text: str) -> int:
    # Claude uses ~4 characters per token on average
    return len(text) // 4
