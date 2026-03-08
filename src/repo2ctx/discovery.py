"""File discovery with gitignore support and glob filtering."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".env",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
    ".svn",
    ".hg",
}

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".o",
    ".a",
    ".pyc",
    ".pyo",
    ".class",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".mp3",
    ".mp4",
    ".wav",
    ".avi",
    ".mov",
    ".sqlite",
    ".db",
    ".DS_Store",
}


@dataclass
class FileInfo:
    path: Path
    relative_path: str
    size: int
    extension: str


def _is_binary(path: Path) -> bool:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except OSError:
        return True


def _should_skip_dir(name: str) -> bool:
    if name.startswith(".") and name != ".github":
        return True
    return name in SKIP_DIRS


def _matches_any(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
        # Also match against basename
        if fnmatch.fnmatch(Path(path).name, pattern):
            return True
        # Match against path segments
        if any(fnmatch.fnmatch(part, pattern) for part in Path(path).parts):
            return True
    return False


def _get_gitignored_files(root: Path) -> set[str]:
    """Get set of gitignored file paths relative to root."""
    try:
        from git import Repo

        repo = Repo(root, search_parent_directories=True)
        # Get all ignored files
        ignored = set()
        try:
            ignored_files = repo.git.ls_files(
                "--others", "--ignored", "--exclude-standard", "--directory"
            )
            if ignored_files:
                for line in ignored_files.strip().split("\n"):
                    if line:
                        ignored.add(line.rstrip("/"))
        except Exception:
            pass
        return ignored
    except Exception:
        return set()


def discover_files(
    root: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[FileInfo]:
    """Discover all relevant source files in a directory.

    Args:
        root: Root directory to scan.
        include: Glob patterns to include (if set, only matching files are included).
        exclude: Glob patterns to exclude.

    Returns:
        List of FileInfo for discovered files.
    """
    root = root.resolve()
    gitignored = _get_gitignored_files(root)
    files: list[FileInfo] = []

    for item in _walk(root, root, gitignored):
        rel = str(item.relative_to(root))

        if include and not _matches_any(rel, include):
            continue
        if exclude and _matches_any(rel, exclude):
            continue

        if _is_binary(item):
            continue

        try:
            size = item.stat().st_size
        except OSError:
            continue

        files.append(
            FileInfo(
                path=item,
                relative_path=rel,
                size=size,
                extension=item.suffix,
            )
        )

    return sorted(files, key=lambda f: f.relative_path)


def _walk(directory: Path, root: Path, gitignored: set[str]):
    """Recursively walk directory, skipping ignored paths."""
    try:
        entries = sorted(directory.iterdir(), key=lambda p: p.name)
    except PermissionError:
        return

    for entry in entries:
        rel = str(entry.relative_to(root))

        if entry.is_dir():
            if _should_skip_dir(entry.name):
                continue
            if rel in gitignored or rel + "/" in gitignored:
                continue
            yield from _walk(entry, root, gitignored)
        elif entry.is_file():
            if rel in gitignored:
                continue
            yield entry


def build_file_tree(files: list[FileInfo]) -> str:
    """Build an ASCII file tree from a list of files."""
    if not files:
        return ""

    lines: list[str] = []
    paths = [f.relative_path for f in files]

    # Build tree structure
    tree_dict: dict = {}
    for p in paths:
        parts = Path(p).parts
        current = tree_dict
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    def _render(d: dict, prefix: str = "") -> None:
        items = sorted(d.items())
        for i, (name, children) in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{name}")
            if children:
                extension = "    " if is_last else "│   "
                _render(children, prefix + extension)

    _render(tree_dict)
    return "\n".join(lines)
