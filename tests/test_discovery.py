"""Tests for file discovery."""

from pathlib import Path

from repo2ctx.discovery import FileInfo, build_file_tree, discover_files


def test_discover_files_basic(tmp_path: Path):
    (tmp_path / "hello.py").write_text("print('hi')")
    (tmp_path / "world.js").write_text("console.log('hi')")
    files = discover_files(tmp_path)
    assert len(files) == 2
    names = {f.relative_path for f in files}
    assert "hello.py" in names
    assert "world.js" in names


def test_discover_files_nested(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import os")
    (tmp_path / "src" / "lib").mkdir()
    (tmp_path / "src" / "lib" / "utils.py").write_text("pass")
    files = discover_files(tmp_path)
    paths = {f.relative_path for f in files}
    assert "src/main.py" in paths
    assert "src/lib/utils.py" in paths


def test_discover_skips_hidden_dirs(tmp_path: Path):
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "secret.py").write_text("pass")
    (tmp_path / "visible.py").write_text("pass")
    files = discover_files(tmp_path)
    assert len(files) == 1
    assert files[0].relative_path == "visible.py"


def test_discover_skips_pycache(tmp_path: Path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "mod.cpython-310.pyc").write_bytes(b"\x00")
    (tmp_path / "mod.py").write_text("pass")
    files = discover_files(tmp_path)
    assert len(files) == 1


def test_discover_skips_binary(tmp_path: Path):
    (tmp_path / "image.png").write_bytes(b"\x89PNG\x00\x00")
    (tmp_path / "code.py").write_text("pass")
    files = discover_files(tmp_path)
    assert len(files) == 1
    assert files[0].relative_path == "code.py"


def test_discover_include_filter(tmp_path: Path):
    (tmp_path / "a.py").write_text("pass")
    (tmp_path / "b.js").write_text("pass")
    (tmp_path / "c.py").write_text("pass")
    files = discover_files(tmp_path, include=["*.py"])
    assert len(files) == 2
    assert all(f.extension == ".py" for f in files)


def test_discover_exclude_filter(tmp_path: Path):
    (tmp_path / "a.py").write_text("pass")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("pass")
    files = discover_files(tmp_path, exclude=["tests"])
    assert len(files) == 1
    assert files[0].relative_path == "a.py"


def test_discover_empty_dir(tmp_path: Path):
    files = discover_files(tmp_path)
    assert files == []


def test_discover_file_info_fields(tmp_path: Path):
    (tmp_path / "test.py").write_text("hello")
    files = discover_files(tmp_path)
    assert len(files) == 1
    fi = files[0]
    assert fi.relative_path == "test.py"
    assert fi.extension == ".py"
    assert fi.size == 5
    assert fi.path == tmp_path / "test.py"


def test_build_file_tree():
    files = [
        FileInfo(Path("a.py"), "a.py", 10, ".py"),
        FileInfo(Path("src/b.py"), "src/b.py", 10, ".py"),
        FileInfo(Path("src/c.py"), "src/c.py", 10, ".py"),
    ]
    result = build_file_tree(files)
    assert "a.py" in result
    assert "src" in result
    assert "b.py" in result
    assert "c.py" in result


def test_build_file_tree_empty():
    assert build_file_tree([]) == ""


def test_discover_keeps_github_dir(tmp_path: Path):
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "workflows").mkdir()
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("name: CI")
    files = discover_files(tmp_path)
    assert len(files) == 1
    assert files[0].relative_path == ".github/workflows/ci.yml"
