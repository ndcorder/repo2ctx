"""Tests for pipeline."""

import os
import stat
from pathlib import Path

from repo2ctx.pipeline import run


def test_pipeline_no_files(tmp_path: Path):
    result = run(tmp_path)
    assert result == "No files found."


def test_pipeline_basic(tmp_path: Path):
    (tmp_path / "hello.py").write_text("print('hello')")
    (tmp_path / "util.py").write_text("x = 1")
    result = run(tmp_path)
    assert "hello.py" in result
    assert "util.py" in result
    assert "print('hello')" in result


def test_pipeline_with_focus(tmp_path: Path):
    (tmp_path / "main.py").write_text("import util")
    (tmp_path / "util.py").write_text("x = 1")
    (tmp_path / "other.py").write_text("y = 2")
    result = run(tmp_path, focus=["main.py"])
    assert "main.py" in result


def test_pipeline_unreadable_file(tmp_path: Path, monkeypatch):
    good = tmp_path / "good.py"
    good.write_text("x = 1")
    bad = tmp_path / "bad.py"
    bad.write_text("y = 2")

    original_read_text = Path.read_text

    def _patched_read_text(self, *args, **kwargs):
        if self.name == "bad.py":
            raise OSError("Permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _patched_read_text)
    result = run(tmp_path)
    assert "good.py" in result


def test_pipeline_format_xml(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1")
    result = run(tmp_path, fmt="xml")
    assert "<repository-context>" in result


def test_pipeline_format_json(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1")
    result = run(tmp_path, fmt="json")
    assert '"files"' in result


def test_pipeline_include_exclude(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1")
    (tmp_path / "b.js").write_text("y = 2")
    result = run(tmp_path, include=["*.py"])
    assert "a.py" in result
    assert "b.js" not in result

    result2 = run(tmp_path, exclude=["*.js"])
    assert "a.py" in result2
