"""Output formatting: Markdown, XML, and JSON."""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from repo2ctx.budget import BudgetAllocation

# Map extensions to markdown language identifiers
LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".xml": "xml",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".R": "r",
    ".lua": "lua",
    ".dart": "dart",
    ".ex": "elixir",
    ".exs": "elixir",
}


def _detect_lang_id(file_path: str) -> str:
    ext = Path(file_path).suffix
    return LANG_MAP.get(ext, "")


def format_output(
    allocations: list[BudgetAllocation],
    file_tree: str,
    fmt: str = "markdown",
    stats: dict | None = None,
) -> str:
    """Format the output in the specified format.

    Args:
        allocations: List of budget allocations with content.
        file_tree: ASCII file tree string.
        fmt: Output format — "markdown", "xml", or "json".
        stats: Optional statistics dict.

    Returns:
        Formatted output string.
    """
    if fmt == "xml":
        return _format_xml(allocations, file_tree, stats)
    elif fmt == "json":
        return _format_json(allocations, file_tree, stats)
    return _format_markdown(allocations, file_tree, stats)


def _format_markdown(
    allocations: list[BudgetAllocation],
    file_tree: str,
    stats: dict | None,
) -> str:
    parts: list[str] = []

    # Header
    parts.append("# Repository Context\n")

    # Stats
    if stats:
        parts.append("## Summary\n")
        for key, value in stats.items():
            parts.append(f"- **{key}**: {value}")
        parts.append("")

    # File tree
    if file_tree:
        parts.append("## File Tree\n")
        parts.append("```")
        parts.append(file_tree)
        parts.append("```\n")

    # Files
    parts.append("## Files\n")
    for alloc in allocations:
        lang_id = _detect_lang_id(alloc.file_path)
        truncated_marker = " (truncated)" if alloc.truncated else ""
        parts.append(f"### `{alloc.file_path}`{truncated_marker}\n")
        parts.append(f"```{lang_id}")
        parts.append(alloc.content)
        parts.append("```\n")

    return "\n".join(parts)


def _format_xml(
    allocations: list[BudgetAllocation],
    file_tree: str,
    stats: dict | None,
) -> str:
    parts: list[str] = []

    parts.append("<repository-context>")

    # Stats
    if stats:
        parts.append("  <summary>")
        for key, value in stats.items():
            safe_key = key.lower().replace(" ", "-")
            parts.append(f"    <{safe_key}>{xml_escape(str(value))}</{safe_key}>")
        parts.append("  </summary>")

    # File tree
    if file_tree:
        parts.append("  <file-tree>")
        parts.append(xml_escape(file_tree))
        parts.append("  </file-tree>")

    # Files
    parts.append("  <files>")
    for alloc in allocations:
        truncated_attr = ' truncated="true"' if alloc.truncated else ""
        escaped_path = xml_escape(alloc.file_path, {'"': "&quot;"})
        parts.append(f'    <file path="{escaped_path}"{truncated_attr}>')
        parts.append(xml_escape(alloc.content))
        parts.append("    </file>")
    parts.append("  </files>")

    parts.append("</repository-context>")
    return "\n".join(parts)


def _format_json(
    allocations: list[BudgetAllocation],
    file_tree: str,
    stats: dict | None,
) -> str:
    data = {
        "summary": stats or {},
        "file_tree": file_tree,
        "files": [
            {
                "path": alloc.file_path,
                "content": alloc.content,
                "tokens": alloc.actual_tokens,
                "truncated": alloc.truncated,
            }
            for alloc in allocations
        ],
    }
    return json.dumps(data, indent=2)
