"""File scoring: git recency, import centrality, and focus proximity."""

from __future__ import annotations

import time
from pathlib import Path

from repo2ctx.graph import DependencyGraph


def git_recency_scores(root: Path, files: list[str]) -> dict[str, float]:
    """Score files by git recency using exponential decay.

    Uses a single `git log` call to batch-extract timestamps,
    avoiding one subprocess per file.

    Returns:
        Dict of file path -> score in [0, 1].
    """
    try:
        from git import Repo

        repo = Repo(root, search_parent_directories=True)
    except Exception:
        return {f: 0.5 for f in files}

    now = time.time()
    decay = 30 * 24 * 3600  # half-life ~30 days

    file_timestamps = _batch_git_timestamps(repo, set(files))

    scores: dict[str, float] = {}
    for filepath in files:
        ts = file_timestamps.get(filepath)
        if ts is not None:
            age_seconds = now - ts
            scores[filepath] = 2.0 ** (-age_seconds / decay)
        else:
            scores[filepath] = 0.1
    return scores


def _batch_git_timestamps(repo, target_files: set[str]) -> dict[str, float]:
    """Get most recent commit timestamp for each file via a single git log call.

    Parses `git log --format=%ct --name-only` output which produces blocks of:
        <timestamp>
        <blank line>
        <filename1>
        <filename2>
        <blank line>
    """
    result: dict[str, float] = {}
    try:
        log_output = repo.git.log("--format=%ct", "--name-only")
    except Exception:
        return result

    if not log_output.strip():
        return result

    current_ts: float | None = None
    for line in log_output.split("\n"):
        line = line.strip()
        if not line:
            current_ts = None
            continue
        # Try to parse as timestamp (integer)
        if current_ts is None:
            try:
                current_ts = float(line)
            except ValueError:
                pass
            continue
        # It's a filename — record if it's a target and not yet seen
        if line in target_files and line not in result:
            result[line] = current_ts

        # Early exit once we've found all files
        if len(result) == len(target_files):
            break

    return result


def focus_scores(
    files: list[str],
    graph: DependencyGraph,
    focus: list[str],
) -> dict[str, float]:
    """Score files by proximity to focus targets.

    Focus targets and their direct import neighbors get high scores.
    """
    scores: dict[str, float] = {f: 0.1 for f in files}

    focus_set = set()
    for f in files:
        for target in focus:
            if f == target or f.startswith(target.rstrip("/") + "/"):
                focus_set.add(f)

    # Focus files get max score
    for f in focus_set:
        scores[f] = 1.0

    # Direct neighbors get high score
    for f in focus_set:
        for neighbor in graph.neighbors(f):
            if neighbor in scores:
                scores[neighbor] = max(scores[neighbor], 0.7)

    return scores


def compute_scores(
    files: list[str],
    graph: DependencyGraph,
    root: Path,
    focus: list[str] | None = None,
) -> dict[str, float]:
    """Compute combined scores for all files.

    Combines:
    - PageRank centrality (weight: 0.4)
    - Git recency (weight: 0.3)
    - Focus proximity (weight: 0.3, or 0.0 if no focus)

    Returns:
        Dict of file path -> combined score.
    """
    pagerank = graph.pagerank()
    recency = git_recency_scores(root, files)

    # Normalize PageRank to [0, 1]
    if pagerank:
        max_pr = max(pagerank.values())
        min_pr = min(pagerank.values())
        pr_range = max_pr - min_pr
        if pr_range > 0:
            pagerank = {k: (v - min_pr) / pr_range for k, v in pagerank.items()}
        else:
            pagerank = {k: 0.5 for k in pagerank}

    if focus:
        focus_sc = focus_scores(files, graph, focus)
        # Weighted combination with focus
        return {
            f: (0.3 * pagerank.get(f, 0.0) + 0.3 * recency.get(f, 0.0) + 0.4 * focus_sc.get(f, 0.0))
            for f in files
        }
    else:
        # No focus: just centrality + recency
        return {f: (0.6 * pagerank.get(f, 0.0) + 0.4 * recency.get(f, 0.0)) for f in files}
