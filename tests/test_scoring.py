"""Tests for scoring."""

from pathlib import Path
from unittest.mock import patch

from repo2ctx.graph import DependencyGraph
from repo2ctx.scoring import compute_scores, focus_scores, git_recency_scores


def test_git_recency_no_repo(tmp_path: Path):
    scores = git_recency_scores(tmp_path, ["a.py", "b.py"])
    assert scores["a.py"] == 0.5
    assert scores["b.py"] == 0.5


def test_focus_scores_direct_match():
    files = ["src/auth.py", "src/db.py", "tests/test.py"]
    graph = DependencyGraph()
    scores = focus_scores(files, graph, ["src/auth.py"])
    assert scores["src/auth.py"] == 1.0
    assert scores["src/db.py"] == 0.1


def test_focus_scores_directory():
    files = ["src/auth/login.py", "src/auth/logout.py", "src/db.py"]
    graph = DependencyGraph()
    scores = focus_scores(files, graph, ["src/auth/"])
    assert scores["src/auth/login.py"] == 1.0
    assert scores["src/auth/logout.py"] == 1.0
    assert scores["src/db.py"] == 0.1


def test_focus_scores_neighbors():
    files = ["a.py", "b.py", "c.py"]
    graph = DependencyGraph()
    graph.add_edge("a.py", "b.py")  # a imports b
    scores = focus_scores(files, graph, ["a.py"])
    assert scores["a.py"] == 1.0
    assert scores["b.py"] == 0.7  # neighbor
    assert scores["c.py"] == 0.1


def test_compute_scores_no_focus(tmp_path: Path):
    files = ["a.py", "b.py"]
    graph = DependencyGraph()
    graph.add_edge("a.py", "b.py")
    scores = compute_scores(files, graph, tmp_path)
    assert len(scores) == 2
    assert all(v > 0 for v in scores.values())


def test_compute_scores_with_focus(tmp_path: Path):
    files = ["a.py", "b.py", "c.py"]
    graph = DependencyGraph()
    graph.add_edge("a.py", "b.py")
    scores = compute_scores(files, graph, tmp_path, focus=["a.py"])
    assert scores["a.py"] > scores["c.py"]
