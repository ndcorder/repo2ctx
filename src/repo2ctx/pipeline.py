"""Main pipeline: orchestrates discovery → graph → scoring → budget → format."""

from __future__ import annotations

from pathlib import Path

from repo2ctx.budget import allocate_budget
from repo2ctx.discovery import build_file_tree, discover_files
from repo2ctx.formats import format_output
from repo2ctx.graph import DependencyGraph
from repo2ctx.imports import detect_language, extract_imports, resolve_import_to_file
from repo2ctx.scoring import compute_scores


def run(
    root: Path,
    max_tokens: int = 128_000,
    focus: list[str] | None = None,
    fmt: str = "markdown",
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    model: str = "openai",
) -> str:
    """Run the full repo2ctx pipeline.

    Args:
        root: Root directory to analyze.
        max_tokens: Token budget.
        focus: Focus paths.
        fmt: Output format (markdown, xml, json).
        include: Include glob patterns.
        exclude: Exclude glob patterns.
        model: Token counting model (openai, claude).

    Returns:
        Formatted context string.
    """
    root = root.resolve()

    # Step 1: Discover files
    file_infos = discover_files(root, include=include, exclude=exclude)
    if not file_infos:
        return "No files found."

    all_paths = [f.relative_path for f in file_infos]

    # Step 2: Read file contents
    file_contents: dict[str, str] = {}
    file_languages: dict[str, str] = {}
    for fi in file_infos:
        try:
            content = fi.path.read_text(encoding="utf-8", errors="replace")
            file_contents[fi.relative_path] = content
            lang = detect_language(fi.path)
            if lang:
                file_languages[fi.relative_path] = lang
        except OSError:
            continue

    # Step 3: Build dependency graph
    graph = DependencyGraph()
    for path in all_paths:
        graph.add_node(path)

    for path, content in file_contents.items():
        lang = file_languages.get(path)
        if lang:
            imports = extract_imports(content.encode("utf-8"), lang)
            for imp in imports:
                resolved = resolve_import_to_file(imp, path, all_paths, lang)
                if resolved:
                    graph.add_edge(path, resolved)

    # Step 4: Compute scores
    scores = compute_scores(all_paths, graph, root, focus=focus)

    # Step 5: Order files by topological sort
    topo_order = graph.topological_sort()
    # Include files not in graph
    ordered_paths = [p for p in topo_order if p in file_contents]
    ordered_set = set(ordered_paths)
    remaining = [p for p in all_paths if p not in ordered_set and p in file_contents]
    ordered_paths.extend(remaining)

    # Reorder file_contents to match
    ordered_contents = {p: file_contents[p] for p in ordered_paths}

    # Step 6: Allocate budget
    allocations = allocate_budget(
        ordered_contents, scores, max_tokens, model=model, languages=file_languages
    )

    # Step 7: Build file tree
    file_tree_str = build_file_tree(file_infos)

    # Step 8: Compute stats
    total_tokens = sum(a.actual_tokens for a in allocations)
    truncated_count = sum(1 for a in allocations if a.truncated)
    stats = {
        "Total files": len(allocations),
        "Total tokens": total_tokens,
        "Token budget": max_tokens,
        "Budget utilization": f"{total_tokens / max_tokens * 100:.1f}%",
        "Files truncated": truncated_count,
        "Token model": model,
    }

    # Step 9: Format output
    return format_output(allocations, file_tree_str, fmt=fmt, stats=stats)
