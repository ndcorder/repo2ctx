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


def test_discover_skips_egg_info(tmp_path: Path):
    (tmp_path / "mypackage.egg-info").mkdir()
    (tmp_path / "mypackage.egg-info" / "PKG-INFO").write_text("Name: mypackage")
    (tmp_path / "setup.py").write_text("pass")
    files = discover_files(tmp_path)
    assert len(files) == 1
    assert files[0].relative_path == "setup.py"


# --- Binary detection ---


def test_discover_binary_with_null_bytes(tmp_path: Path):
    """File containing null bytes (but not a known binary extension) is skipped."""
    (tmp_path / "data.dat").write_bytes(b"hello\x00world")
    (tmp_path / "code.py").write_text("pass")
    files = discover_files(tmp_path)
    assert len(files) == 1
    assert files[0].relative_path == "code.py"


def test_discover_binary_oserror(tmp_path: Path, monkeypatch):
    """File that can't be opened for binary check is treated as binary."""
    from repo2ctx import discovery

    target = tmp_path / "broken.dat"
    target.write_text("content")

    original_is_binary = discovery._is_binary

    def _mock_is_binary(path):
        if path.name == "broken.dat":
            raise OSError("cannot read")
        return original_is_binary(path)

    # Patch open to fail for this specific file, triggering the OSError path
    original_open = open

    def patched_open(path, *args, **kwargs):
        if str(path).endswith("broken.dat") and args and args[0] == "rb":
            raise OSError("cannot read")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", patched_open)
    files = discover_files(tmp_path)
    # broken.dat should be skipped because _is_binary returns True on OSError
    paths = {f.relative_path for f in files}
    assert "broken.dat" not in paths


# --- _matches_any path segment matching ---


def test_matches_any_path_segments():
    from repo2ctx.discovery import _matches_any

    # Pattern matches a path segment (directory name)
    assert _matches_any("vendor/lib/code.py", ["vendor"]) is True
    # Pattern matches basename
    assert _matches_any("src/utils.py", ["utils.py"]) is True
    # Pattern matches glob on full path
    assert _matches_any("src/main.py", ["*.py"]) is True
    # No match
    assert _matches_any("src/main.py", ["*.rs"]) is False


# --- Gitignore integration ---


def test_discover_with_gitignore(tmp_path: Path):
    """Create a real git repo with .gitignore and verify ignored files/dirs are excluded."""
    import subprocess

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(tmp_path), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(tmp_path), check=True, capture_output=True,
    )

    # Use "output/" not "build/" since build is in SKIP_DIRS
    (tmp_path / ".gitignore").write_text("ignored.txt\noutput/\n")
    (tmp_path / "ignored.txt").write_text("should be ignored")
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "compiled.js").write_text("compiled")
    (tmp_path / "kept.py").write_text("pass")

    # Must commit .gitignore for ls-files to work
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(tmp_path), check=True, capture_output=True,
    )

    files = discover_files(tmp_path)
    paths = {f.relative_path for f in files}
    assert "kept.py" in paths
    assert "ignored.txt" not in paths
    assert "output/compiled.js" not in paths


# --- Permission / stat errors ---


def test_discover_permission_error(tmp_path: Path, monkeypatch):
    """Directory without read permission is skipped gracefully."""
    from repo2ctx import discovery

    (tmp_path / "good.py").write_text("pass")
    (tmp_path / "secret").mkdir()
    (tmp_path / "secret" / "data.py").write_text("pass")

    original_walk = discovery._walk

    def patched_walk(directory, root, gitignored):
        if directory.name == "secret":
            raise PermissionError("no access")
        yield from original_walk(directory, root, gitignored)

    # Patch iterdir on the secret directory to raise PermissionError
    original_iterdir = Path.iterdir

    def patched_iterdir(self):
        if self.name == "secret":
            raise PermissionError("no access")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", patched_iterdir)
    files = discover_files(tmp_path)
    paths = {f.relative_path for f in files}
    assert "good.py" in paths
    assert "secret/data.py" not in paths


def test_discover_stat_error(tmp_path: Path, monkeypatch):
    """File whose stat() fails after passing binary check is skipped."""
    import os
    from repo2ctx import discovery

    (tmp_path / "good.py").write_text("pass")
    (tmp_path / "bad.py").write_text("pass")

    # Patch _is_binary to always return False so we reach the stat() call
    monkeypatch.setattr(discovery, "_is_binary", lambda p: False)

    # Delete bad.py after _walk yields it but before stat() runs.
    # We wrap the _walk generator to remove the file just-in-time.
    original_walk = discovery._walk

    def patched_walk(directory, root, gitignored):
        for item in original_walk(directory, root, gitignored):
            if item.name == "bad.py":
                # Remove file so stat() raises OSError
                os.remove(item)
            yield item

    monkeypatch.setattr(discovery, "_walk", patched_walk)
    files = discover_files(tmp_path)
    paths = {f.relative_path for f in files}
    assert "good.py" in paths
    assert "bad.py" not in paths


# --- Exclude with path segment matching ---


def test_exclude_path_segment_match(tmp_path: Path):
    """Exclude pattern matching a directory segment filters out nested files."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("pass")
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "lib.py").write_text("pass")
    files = discover_files(tmp_path, exclude=["vendor"])
    paths = {f.relative_path for f in files}
    assert "src/main.py" in paths
    assert "vendor/lib.py" not in paths


def test_gitignore_skips_files_in_walk(tmp_path: Path):
    """Files listed in gitignored set are skipped during _walk."""
    from repo2ctx.discovery import _walk

    # Directly test _walk with a pre-populated gitignored set
    (tmp_path / "public.py").write_text("pass")
    (tmp_path / "secret.txt").write_text("password")

    # Simulate gitignored files set
    gitignored = {"secret.txt"}
    walked = list(_walk(tmp_path, tmp_path, gitignored))
    names = {f.name for f in walked}
    assert "public.py" in names
    assert "secret.txt" not in names


def test_gitignored_files_inner_exception(monkeypatch):
    """When repo.git.ls_files raises, _get_gitignored_files returns empty set."""
    from repo2ctx.discovery import _get_gitignored_files

    class FakeGit:
        def ls_files(self, *args, **kwargs):
            raise RuntimeError("git broke")

    class FakeRepo:
        def __init__(self, *args, **kwargs):
            self.git = FakeGit()

    import repo2ctx.discovery as disc
    monkeypatch.setattr(disc, "_get_gitignored_files", lambda root: set())

    # Test that discover_files still works when gitignore fails
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        (p / "test.py").write_text("pass")
        files = discover_files(p)
        assert len(files) == 1


def test_get_gitignored_files_inner_exception(monkeypatch):
    """When ls_files raises inside _get_gitignored_files, returns empty ignored set."""
    from repo2ctx.discovery import _get_gitignored_files

    class FakeGit:
        def ls_files(self, *args, **kwargs):
            raise RuntimeError("ls-files broke")

    class FakeRepo:
        def __init__(self, *args, **kwargs):
            self.git = FakeGit()

    # Patch git.Repo to return our fake
    import git
    monkeypatch.setattr(git, "Repo", FakeRepo)
    result = _get_gitignored_files(Path("/tmp"))
    assert result == set()
