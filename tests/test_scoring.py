"""Tests for scoring."""

from pathlib import Path

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


# --- Tests for git_recency_scores success path & _batch_git_timestamps ---

from repo2ctx.scoring import _batch_git_timestamps


class _MockGit:
    def __init__(self, log_output: str):
        self._log_output = log_output

    def log(self, *args):
        return self._log_output


class _MockRepo:
    def __init__(self, log_output: str):
        self.git = _MockGit(log_output)


def test_batch_git_timestamps_parsing():
    # Format: timestamp then filenames, blank line separates commits
    log_output = "1700000000\na.py\nb.py\n\n1699000000\nc.py\n"
    repo = _MockRepo(log_output)
    result = _batch_git_timestamps(repo, {"a.py", "b.py", "c.py"})
    assert result["a.py"] == 1700000000.0
    assert result["b.py"] == 1700000000.0
    assert result["c.py"] == 1699000000.0


def test_batch_git_timestamps_empty_log():
    repo = _MockRepo("")
    result = _batch_git_timestamps(repo, {"a.py"})
    assert result == {}


def test_batch_git_timestamps_empty_log_whitespace():
    repo = _MockRepo("   \n  ")
    result = _batch_git_timestamps(repo, {"a.py"})
    assert result == {}


def test_batch_git_timestamps_early_exit():
    # Only looking for a.py — should stop after first commit block
    log_output = "1700000000\na.py\n\n1699000000\nb.py\n"
    repo = _MockRepo(log_output)
    result = _batch_git_timestamps(repo, {"a.py"})
    assert result == {"a.py": 1700000000.0}


def test_batch_git_timestamps_keeps_first_occurrence():
    # a.py appears in both commits; should keep the first (most recent)
    log_output = "1700000000\na.py\n\n1699000000\na.py\n"
    repo = _MockRepo(log_output)
    result = _batch_git_timestamps(repo, {"a.py"})
    assert result["a.py"] == 1700000000.0


def test_batch_git_timestamps_exception():
    class _BadGit:
        def log(self, *args):
            raise RuntimeError("git broken")

    class _BadRepo:
        git = _BadGit()

    result = _batch_git_timestamps(_BadRepo(), {"a.py"})
    assert result == {}


def test_batch_git_timestamps_invalid_line_as_timestamp():
    # Non-numeric line where timestamp expected triggers ValueError branch
    log_output = "not_a_number\n\n1700000000\na.py\n"
    repo = _MockRepo(log_output)
    result = _batch_git_timestamps(repo, {"a.py"})
    assert result["a.py"] == 1700000000.0


def test_git_recency_with_repo(monkeypatch, tmp_path: Path):
    import time

    now = time.time()
    recent_ts = int(now - 3600)  # 1 hour ago
    old_ts = int(now - 90 * 24 * 3600)  # 90 days ago
    log_output = f"{recent_ts}\na.py\n\n{old_ts}\nb.py\n"

    class _FakeRepo:
        def __init__(self, *a, **kw):
            self.git = _MockGit(log_output)

    import git as git_module
    monkeypatch.setattr(git_module, "Repo", _FakeRepo)

    scores = git_recency_scores(tmp_path, ["a.py", "b.py"])
    # Recent file should score higher than old file
    assert scores["a.py"] > scores["b.py"]
    assert 0 < scores["a.py"] <= 1.0
    assert 0 < scores["b.py"] <= 1.0


def test_git_recency_file_not_in_log(monkeypatch, tmp_path: Path):
    log_output = "1700000000\na.py\n"

    class _FakeRepo:
        def __init__(self, *a, **kw):
            self.git = _MockGit(log_output)

    import git as git_module
    monkeypatch.setattr(git_module, "Repo", _FakeRepo)

    scores = git_recency_scores(tmp_path, ["a.py", "missing.py"])
    assert scores["a.py"] > 0
    assert scores["missing.py"] == 0.1


def test_compute_scores_equal_pagerank(monkeypatch, tmp_path: Path):
    # All nodes have same PageRank → pr_range == 0 → all get 0.5
    files = ["a.py", "b.py", "c.py"]
    graph = DependencyGraph()
    # No edges → all PageRank values equal
    for f in files:
        graph.add_node(f)

    # Mock git to avoid repo lookup
    monkeypatch.setattr(
        "repo2ctx.scoring.git_recency_scores",
        lambda root, files: {f: 0.5 for f in files},
    )

    scores = compute_scores(files, graph, tmp_path)
    # With equal PageRank (all 0.5) and equal recency (all 0.5):
    # score = 0.6 * 0.5 + 0.4 * 0.5 = 0.5
    for f in files:
        assert scores[f] == 0.5
