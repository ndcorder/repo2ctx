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
