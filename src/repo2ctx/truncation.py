"""Smart truncation: preserve signatures and docstrings, remove bodies."""

from __future__ import annotations

from repo2ctx.imports import _get_parser
from repo2ctx.tokens import count_tokens

# Node types that represent function/class definitions by language
DEFINITION_TYPES: dict[str, set[str]] = {
    "python": {"function_definition", "class_definition"},
    "javascript": {"function_declaration", "class_declaration", "method_definition",
                   "arrow_function", "function"},
    "typescript": {"function_declaration", "class_declaration", "method_definition",
                   "arrow_function", "function"},
    "tsx": {"function_declaration", "class_declaration", "method_definition",
            "arrow_function", "function"},
    "go": {"function_declaration", "method_declaration"},
    "rust": {"function_item", "impl_item", "struct_item", "enum_item"},
}

BODY_TYPES: dict[str, str] = {
    "python": "block",
    "javascript": "statement_block",
    "typescript": "statement_block",
    "tsx": "statement_block",
    "go": "block",
    "rust": "block",
}


def smart_truncate(source: str, language: str, max_tokens: int, model: str = "openai") -> str:
    """Truncate source code intelligently, preserving structure.

    Keeps:
    - Import statements
    - Class/function signatures
    - Docstrings
    - Type definitions

    Removes:
    - Function/method bodies (replaced with ...)

    Args:
        source: Source code text.
        language: Language identifier.
        max_tokens: Maximum token budget.
        model: Token counting model.

    Returns:
        Truncated source code.
    """
    current_tokens = count_tokens(source, model)
    if current_tokens <= max_tokens:
        return source

    parser = _get_parser(language)
    if parser is None:
        return _naive_truncate(source, max_tokens, model)

    source_bytes = source.encode("utf-8")
    parsed = parser.parse(source_bytes)
    root = parsed.root_node

    # Collect all body nodes that can be truncated
    bodies = _find_truncatable_bodies(root, language)

    if not bodies:
        return _naive_truncate(source, max_tokens, model)

    # Sort bodies by size (largest first) — truncate biggest bodies first
    bodies.sort(key=lambda n: n.end_byte - n.start_byte, reverse=True)

    lines = source.split("\n")
    truncated_ranges: list[tuple[int, int, str]] = []

    for body_node in bodies:
        start_line = body_node.start_point[0]
        end_line = body_node.end_point[0]

        # Check if this body has a docstring as the first statement
        has_docstring = False
        docstring_end_line = start_line
        if language == "python" and body_node.children:
            first_child = body_node.children[0]
            if first_child.type == "expression_statement" and first_child.children:
                expr = first_child.children[0]
                if expr.type == "string":
                    has_docstring = True
                    docstring_end_line = expr.end_point[0]

        # Get indentation of the body
        if start_line < len(lines):
            indent = _get_indent(lines[start_line])
        else:
            indent = "    "

        # Replace body content (after docstring) with ...
        if has_docstring and docstring_end_line < end_line:
            # Keep docstring, truncate rest
            truncated_ranges.append((docstring_end_line + 1, end_line, f"{indent}..."))
        else:
            truncated_ranges.append((start_line, end_line, f"{indent}..."))

        # Check if we're under budget now
        result = _apply_truncations(lines, truncated_ranges)
        if count_tokens(result, model) <= max_tokens:
            return result

    # Apply all truncations
    result = _apply_truncations(lines, truncated_ranges)
    if count_tokens(result, model) <= max_tokens:
        return result

    # Still over budget — naive truncate the result
    return _naive_truncate(result, max_tokens, model)


def _find_truncatable_bodies(node, language: str) -> list:
    """Find all function/method body nodes that can be truncated."""
    bodies = []
    def_types = DEFINITION_TYPES.get(language, set())
    body_type = BODY_TYPES.get(language, "block")

    for child in _traverse_definitions(node, def_types):
        for sub in child.children:
            if sub.type == body_type:
                bodies.append(sub)
                break

    return bodies


def _traverse_definitions(node, def_types: set[str]) -> list:
    """Find all definition nodes in the tree."""
    results = []
    if node.type in def_types:
        results.append(node)
    for child in node.children:
        results.extend(_traverse_definitions(child, def_types))
    return results


def _apply_truncations(lines: list[str], ranges: list[tuple[int, int, str]]) -> str:
    """Apply truncation ranges to source lines."""
    # Sort ranges by start line
    sorted_ranges = sorted(ranges, key=lambda r: r[0])

    result_lines: list[str] = []
    skip_until = -1

    for i, line in enumerate(lines):
        if i <= skip_until:
            continue

        truncated = False
        for start, end, replacement in sorted_ranges:
            if i == start:
                result_lines.append(replacement)
                skip_until = end
                truncated = True
                break
            elif start < i <= end:
                truncated = True
                break

        if not truncated:
            result_lines.append(line)

    return "\n".join(result_lines)


def _get_indent(line: str) -> str:
    """Extract leading whitespace from a line."""
    return line[: len(line) - len(line.lstrip())]


def _naive_truncate(source: str, max_tokens: int, model: str) -> str:
    """Simple line-based truncation as fallback."""
    lines = source.split("\n")
    result_lines: list[str] = []
    token_count = 0

    for line in lines:
        line_tokens = count_tokens(line + "\n", model)
        if token_count + line_tokens > max_tokens:
            result_lines.append("... (truncated)")
            break
        result_lines.append(line)
        token_count += line_tokens

    return "\n".join(result_lines)
