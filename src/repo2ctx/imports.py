"""Import extraction using tree-sitter for multiple languages."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Language, Parser

LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
}


def detect_language(path: Path) -> str | None:
    """Detect programming language from file extension."""
    return LANGUAGE_MAP.get(path.suffix.lower())


def get_parser(language: str) -> Parser | None:
    """Get a tree-sitter parser for the given language."""
    try:
        lang_obj = _get_language(language)
        if lang_obj is None:
            return None
        return Parser(lang_obj)
    except Exception:
        return None


def _get_language(language: str) -> Language | None:
    """Get tree-sitter Language object."""
    try:
        if language == "python":
            import tree_sitter_python as tsp

            return Language(tsp.language())
        elif language == "javascript":
            import tree_sitter_javascript as tsjs

            return Language(tsjs.language())
        elif language in ("typescript", "tsx"):
            import tree_sitter_typescript as tsts

            if language == "tsx":
                return Language(tsts.language_tsx())
            return Language(tsts.language_typescript())
        elif language == "go":
            import tree_sitter_go as tsgo

            return Language(tsgo.language())
        elif language == "rust":
            import tree_sitter_rust as tsrs

            return Language(tsrs.language())
    except ImportError:
        pass
    return None


def extract_imports(source: bytes, language: str) -> list[str]:
    """Extract import/dependency references from source code.

    Args:
        source: Raw source bytes.
        language: Language identifier (python, javascript, typescript, tsx, go, rust).

    Returns:
        List of imported module/file names.
    """
    parser = get_parser(language)
    if parser is None:
        return _extract_imports_regex(source.decode("utf-8", errors="replace"), language)

    parsed = parser.parse(source)
    root = parsed.root_node

    if language == "python":
        return _extract_python_imports(root)
    elif language in ("javascript", "typescript", "tsx"):
        return _extract_js_imports(root)
    elif language == "go":
        return _extract_go_imports(root)
    elif language == "rust":
        return _extract_rust_imports(root)
    return []


def _extract_python_imports(root) -> list[str]:
    imports: list[str] = []
    for node in _traverse(root):
        if node.type == "import_statement":
            for child in node.children:
                if child.type == "dotted_name":
                    imports.append(child.text.decode())
        elif node.type == "import_from_statement":
            for child in node.children:
                if child.type == "dotted_name":
                    imports.append(child.text.decode())
                    break
                elif child.type == "relative_import":
                    # from . import X or from .foo import X
                    text = child.text.decode()
                    imports.append(text)
                    break
    return imports


def _extract_js_imports(root) -> list[str]:
    imports: list[str] = []
    for node in _traverse(root):
        if node.type == "import_statement":
            for child in node.children:
                if child.type == "string":
                    val = child.text.decode().strip("'\"")
                    imports.append(val)
        elif node.type == "call_expression":
            if node.children and node.children[0].type == "identifier":
                if node.children[0].text == b"require":
                    for child in node.children:
                        if child.type == "arguments":
                            for arg in child.children:
                                if arg.type == "string":
                                    val = arg.text.decode().strip("'\"")
                                    imports.append(val)
    return imports


def _extract_go_imports(root) -> list[str]:
    imports: list[str] = []
    for node in _traverse(root):
        if node.type == "import_spec":
            for child in node.children:
                if child.type == "interpreted_string_literal":
                    val = child.text.decode().strip('"')
                    imports.append(val)
    return imports


def _extract_rust_imports(root) -> list[str]:
    imports: list[str] = []
    for node in _traverse(root):
        if node.type == "use_declaration":
            # Extract the path from use declarations
            for child in node.children:
                if child.type in (
                    "scoped_identifier",
                    "identifier",
                    "use_wildcard",
                    "scoped_use_list",
                ):
                    text = child.text.decode()
                    # Get the top-level crate name
                    top = text.split("::")[0]
                    if top:
                        imports.append(top)
                    break
        elif node.type == "extern_crate_declaration":
            for child in node.children:
                if child.type == "identifier":
                    imports.append(child.text.decode())
    return imports


def _traverse(node):
    """Depth-first traversal of tree-sitter nodes."""
    yield node
    for child in node.children:
        yield from _traverse(child)


def _extract_imports_regex(source: str, language: str) -> list[str]:
    """Fallback regex-based import extraction for unsupported languages."""
    import re

    imports: list[str] = []

    if language == "python":
        for m in re.finditer(r"^\s*import\s+([\w.]+)", source, re.MULTILINE):
            imports.append(m.group(1))
        for m in re.finditer(r"^\s*from\s+([\w.]+)\s+import", source, re.MULTILINE):
            imports.append(m.group(1))
    elif language in ("javascript", "typescript", "tsx"):
        for m in re.finditer(r"""(?:import|require)\s*\(?\s*['"]([^'"]+)['"]""", source):
            imports.append(m.group(1))
    elif language == "go":
        for m in re.finditer(r'"([^"]+)"', source):
            imports.append(m.group(1))
    elif language == "rust":
        for m in re.finditer(r"^\s*use\s+([\w:]+)", source, re.MULTILINE):
            imports.append(m.group(1).split("::")[0])
        for m in re.finditer(r"^\s*extern\s+crate\s+(\w+)", source, re.MULTILINE):
            imports.append(m.group(1))

    return imports


def resolve_import_to_file(
    import_name: str,
    source_file: str,
    all_files: list[str],
    language: str,
) -> str | None:
    """Try to resolve an import name to a file path in the project.

    Args:
        import_name: The imported module/path name.
        source_file: Path of the file containing the import.
        all_files: All file paths in the project.
        language: Language of the source file.

    Returns:
        Resolved file path or None if not found.
    """
    if language == "python":
        return _resolve_python_import(import_name, source_file, all_files)
    elif language in ("javascript", "typescript", "tsx"):
        return _resolve_js_import(import_name, source_file, all_files)
    return None


def _resolve_python_import(import_name: str, source_file: str, all_files: list[str]) -> str | None:
    # Convert dotted path to file path
    parts = import_name.split(".")
    candidates = [
        "/".join(parts) + ".py",
        "/".join(parts) + "/__init__.py",
    ]

    file_set = set(all_files)
    for candidate in candidates:
        if candidate in file_set:
            return candidate

    # Try partial matches (e.g., import foo.bar might match foo/bar.py)
    for f in all_files:
        if f.endswith(".py"):
            module_path = f.replace("/", ".").removesuffix(".py").removesuffix(".__init__")
            if module_path == import_name or module_path.endswith("." + import_name):
                return f
    return None


def _resolve_js_import(import_name: str, source_file: str, all_files: list[str]) -> str | None:
    if not import_name.startswith("."):
        return None  # External package

    source_dir = str(Path(source_file).parent)
    # Resolve relative import
    if source_dir == ".":
        resolved = import_name.lstrip("./")
    else:
        resolved = str(Path(source_dir) / import_name)

    # Normalize path
    resolved = str(Path(resolved))

    file_set = set(all_files)
    extensions = ["", ".js", ".ts", ".jsx", ".tsx", "/index.js", "/index.ts"]
    for ext in extensions:
        candidate = resolved + ext
        if candidate in file_set:
            return candidate
    return None
