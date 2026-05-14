"""Tests for import extraction."""

from pathlib import Path

from repo2ctx.imports import (
    detect_language,
    extract_imports,
    resolve_import_to_file,
)

# --- Language detection ---


def test_detect_python():
    assert detect_language(Path("foo.py")) == "python"


def test_detect_javascript():
    assert detect_language(Path("foo.js")) == "javascript"
    assert detect_language(Path("foo.jsx")) == "javascript"


def test_detect_typescript():
    assert detect_language(Path("foo.ts")) == "typescript"
    assert detect_language(Path("foo.tsx")) == "tsx"


def test_detect_go():
    assert detect_language(Path("foo.go")) == "go"


def test_detect_rust():
    assert detect_language(Path("foo.rs")) == "rust"


def test_detect_unknown():
    assert detect_language(Path("foo.txt")) is None
    assert detect_language(Path("foo.md")) is None


# --- Python imports ---


def test_python_import():
    source = b"import os\nimport sys"
    result = extract_imports(source, "python")
    assert "os" in result
    assert "sys" in result


def test_python_from_import():
    source = b"from pathlib import Path\nfrom os.path import join"
    result = extract_imports(source, "python")
    assert "pathlib" in result
    assert "os.path" in result


def test_python_mixed_imports():
    source = b"import json\nfrom collections import defaultdict\nimport re"
    result = extract_imports(source, "python")
    assert set(result) == {"json", "collections", "re"}


# --- JavaScript imports ---


def test_js_import():
    source = b"import React from 'react';\nimport { useState } from 'react';"
    result = extract_imports(source, "javascript")
    assert "react" in result


def test_js_require():
    source = b"const fs = require('fs');\nconst path = require('path');"
    result = extract_imports(source, "javascript")
    assert "fs" in result
    assert "path" in result


def test_js_relative_import():
    source = b"import { foo } from './utils';"
    result = extract_imports(source, "javascript")
    assert "./utils" in result


# --- TypeScript imports ---


def test_ts_import():
    source = b"import { Component } from '@angular/core';"
    result = extract_imports(source, "typescript")
    assert "@angular/core" in result


# --- Go imports ---


def test_go_single_import():
    source = b'package main\n\nimport "fmt"'
    result = extract_imports(source, "go")
    assert "fmt" in result


def test_go_grouped_import():
    source = b'package main\n\nimport (\n\t"fmt"\n\t"os"\n)'
    result = extract_imports(source, "go")
    assert "fmt" in result
    assert "os" in result


# --- Rust imports ---


def test_rust_use():
    source = b"use std::collections::HashMap;"
    result = extract_imports(source, "rust")
    assert "std" in result


def test_rust_extern_crate():
    source = b"extern crate serde;"
    result = extract_imports(source, "rust")
    assert "serde" in result


# --- Import resolution ---


def test_resolve_python_import():
    files = ["foo.py", "bar/baz.py", "bar/__init__.py"]
    assert resolve_import_to_file("foo", "main.py", files, "python") == "foo.py"


def test_resolve_python_dotted_import():
    files = ["foo.py", "bar/baz.py", "bar/__init__.py"]
    assert resolve_import_to_file("bar.baz", "main.py", files, "python") == "bar/baz.py"


def test_resolve_python_package_import():
    files = ["pkg/__init__.py", "pkg/mod.py"]
    assert resolve_import_to_file("pkg", "main.py", files, "python") == "pkg/__init__.py"


def test_resolve_js_relative():
    files = ["src/utils.js", "src/main.js"]
    result = resolve_import_to_file("./utils", "src/main.js", files, "javascript")
    assert result == "src/utils.js"


def test_resolve_external_returns_none():
    files = ["src/main.js"]
    assert resolve_import_to_file("react", "src/main.js", files, "javascript") is None


def test_resolve_nonexistent_returns_none():
    files = ["foo.py"]
    assert resolve_import_to_file("bar", "main.py", files, "python") is None


# --- TSX imports ---


def test_tsx_import():
    source = b"import React from 'react';\nimport { Component } from './MyComponent';"
    result = extract_imports(source, "tsx")
    assert "react" in result
    assert "./MyComponent" in result


# --- get_parser edge cases ---


def test_get_parser_unknown_language():
    from repo2ctx.imports import get_parser

    assert get_parser("cobol") is None


def test_get_parser_exception_path(monkeypatch):
    """When _get_language raises, get_parser returns None."""
    from repo2ctx import imports

    def _explode(lang):
        raise RuntimeError("boom")

    monkeypatch.setattr(imports, "_get_language", _explode)
    assert imports.get_parser("python") is None


# --- Regex fallback ---


def test_extract_imports_regex_python():
    from repo2ctx.imports import _extract_imports_regex

    src = "import os\nfrom pathlib import Path"
    result = _extract_imports_regex(src, "python")
    assert "os" in result
    assert "pathlib" in result


def test_extract_imports_regex_javascript():
    from repo2ctx.imports import _extract_imports_regex

    # The JS regex matches: require('x') and import 'x' / import('x')
    # Standard `import { foo } from 'bar'` doesn't match the regex pattern
    src = "const x = require('baz');\nimport 'bar';"
    result = _extract_imports_regex(src, "javascript")
    assert "baz" in result
    assert "bar" in result


def test_extract_imports_regex_go():
    from repo2ctx.imports import _extract_imports_regex

    src = 'import (\n\t"fmt"\n\t"os"\n)'
    result = _extract_imports_regex(src, "go")
    assert "fmt" in result
    assert "os" in result


def test_extract_imports_regex_rust():
    from repo2ctx.imports import _extract_imports_regex

    src = "use std::collections::HashMap;\nextern crate serde;"
    result = _extract_imports_regex(src, "rust")
    assert "std" in result
    assert "serde" in result


def test_extract_imports_unsupported_falls_back_to_regex(monkeypatch):
    """When tree-sitter parser is None, falls back to regex."""
    from repo2ctx import imports

    monkeypatch.setattr(imports, "get_parser", lambda lang: None)
    source = b"import os\nfrom sys import argv"
    result = imports.extract_imports(source, "python")
    assert "os" in result
    assert "sys" in result


# --- Rust extern crate via tree-sitter ---


def test_rust_extern_crate_extraction():
    source = b"extern crate serde;\nextern crate tokio;"
    result = extract_imports(source, "rust")
    assert "serde" in result
    assert "tokio" in result


# --- Resolve edge cases ---


def test_resolve_python_partial_match():
    """Partial match: import 'bar' matches 'foo/bar.py' via endswith."""
    files = ["src/foo/bar.py"]
    result = resolve_import_to_file("bar", "main.py", files, "python")
    assert result == "src/foo/bar.py"


def test_resolve_js_relative_with_extensions():
    files = ["src/utils.ts", "src/main.ts"]
    result = resolve_import_to_file("./utils", "src/main.ts", files, "typescript")
    assert result == "src/utils.ts"


def test_resolve_js_relative_index():
    files = ["src/components/index.js", "src/main.js"]
    result = resolve_import_to_file("./components", "src/main.js", files, "javascript")
    assert result == "src/components/index.js"


def test_resolve_js_relative_tsx():
    files = ["src/App.tsx", "src/main.tsx"]
    result = resolve_import_to_file("./App", "src/main.tsx", files, "tsx")
    assert result == "src/App.tsx"


def test_resolve_unsupported_language():
    files = ["main.go"]
    assert resolve_import_to_file("fmt", "main.go", files, "go") is None


def test_resolve_js_from_root_dir():
    """Source file at root (source_dir = '.') resolves relative import."""
    files = ["utils.js"]
    result = resolve_import_to_file("./utils", "main.js", files, "javascript")
    assert result == "utils.js"


def test_resolve_js_relative_no_match():
    """Relative JS import that doesn't match any file returns None."""
    files = ["src/other.js"]
    result = resolve_import_to_file("./missing", "src/main.js", files, "javascript")
    assert result is None


def test_get_language_import_error(monkeypatch):
    """ImportError in _get_language returns None and is caught."""
    import builtins
    from repo2ctx.imports import _get_language

    real_import = builtins.__import__

    def failing_import(name, *args, **kwargs):
        if name == "tree_sitter_python":
            raise ImportError("no module")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", failing_import)
    assert _get_language("python") is None


def test_python_relative_import():
    """from .foo import bar uses relative_import node type."""
    source = b"from . import sibling\nfrom .sub import helper"
    result = extract_imports(source, "python")
    assert "." in result or ".sub" in result
    assert len(result) >= 1


def test_extract_imports_unknown_language_with_parser(monkeypatch):
    """When parser succeeds but language isn't in the if/elif chain, returns []."""
    from repo2ctx import imports

    # Make get_parser return a real parser for a fake language
    real_parser = imports.get_parser("python")
    monkeypatch.setattr(imports, "get_parser", lambda lang: real_parser)
    result = imports.extract_imports(b"some code", "haskell")
    assert result == []
