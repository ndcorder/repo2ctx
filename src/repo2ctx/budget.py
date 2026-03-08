"""Token budget allocation across files."""

from __future__ import annotations

from dataclasses import dataclass

from repo2ctx.tokens import count_tokens
from repo2ctx.truncation import smart_truncate


@dataclass
class BudgetAllocation:
    file_path: str
    allocated_tokens: int
    actual_tokens: int
    content: str
    truncated: bool


def allocate_budget(
    files: dict[str, str],
    scores: dict[str, float],
    max_tokens: int,
    model: str = "openai",
    languages: dict[str, str] | None = None,
) -> list[BudgetAllocation]:
    """Allocate token budget across files proportionally to their scores.

    Args:
        files: Dict of file path -> file content.
        scores: Dict of file path -> importance score.
        max_tokens: Total token budget.
        model: Token counting model.
        languages: Dict of file path -> language (for smart truncation).

    Returns:
        List of BudgetAllocation with content (possibly truncated).
    """
    if not files:
        return []

    # Reserve some tokens for formatting overhead (file headers, tree, etc.)
    overhead_ratio = 0.1
    available = int(max_tokens * (1 - overhead_ratio))

    # Calculate total score
    total_score = sum(scores.get(f, 0.01) for f in files)
    if total_score == 0:
        total_score = len(files) * 0.01

    # First pass: count actual tokens and allocate proportionally
    file_tokens: dict[str, int] = {}
    for path, content in files.items():
        file_tokens[path] = count_tokens(content, model)

    total_actual = sum(file_tokens.values())

    if total_actual <= available:
        # Everything fits — no truncation needed
        return [
            BudgetAllocation(
                file_path=path,
                allocated_tokens=file_tokens[path],
                actual_tokens=file_tokens[path],
                content=content,
                truncated=False,
            )
            for path, content in files.items()
        ]

    # Allocate proportionally to scores
    allocations: list[BudgetAllocation] = []
    for path, content in files.items():
        score = scores.get(path, 0.01)
        allocated = int((score / total_score) * available)
        allocated = max(allocated, 50)  # Minimum 50 tokens per file

        actual = file_tokens[path]
        if actual <= allocated:
            allocations.append(
                BudgetAllocation(
                    file_path=path,
                    allocated_tokens=allocated,
                    actual_tokens=actual,
                    content=content,
                    truncated=False,
                )
            )
        else:
            lang = (languages or {}).get(path)
            if lang:
                truncated_content = smart_truncate(content, lang, allocated, model)
            else:
                truncated_content = _simple_truncate(content, allocated, model)
            allocations.append(
                BudgetAllocation(
                    file_path=path,
                    allocated_tokens=allocated,
                    actual_tokens=count_tokens(truncated_content, model),
                    content=truncated_content,
                    truncated=True,
                )
            )

    return allocations


def _simple_truncate(content: str, max_tokens: int, model: str) -> str:
    """Simple line-based truncation."""
    lines = content.split("\n")
    result: list[str] = []
    tokens = 0
    for line in lines:
        line_tokens = count_tokens(line + "\n", model)
        if tokens + line_tokens > max_tokens:
            result.append("... (truncated)")
            break
        result.append(line)
        tokens += line_tokens
    return "\n".join(result)
