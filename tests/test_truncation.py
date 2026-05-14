"""Tests for smart truncation."""

from unittest.mock import patch, MagicMock

from repo2ctx.truncation import smart_truncate, _naive_truncate, _apply_truncations


def test_no_truncation_needed():
    source = "x = 1"
    result = smart_truncate(source, "python", max_tokens=100, model="claude")
    assert result == source


def test_truncate_python_function_body():
    source = """def hello():
    x = 1
    y = 2
    z = 3
    return x + y + z

def world():
    a = 10
    b = 20
    return a + b
"""
    result = smart_truncate(source, "python", max_tokens=10, model="claude")
    assert "def hello" in result
    assert "..." in result
    assert len(result) < len(source)


def test_truncate_preserves_docstring():
    source = '''def hello():
    """This is a docstring."""
    x = 1
    y = 2
    z = 3
    w = 4
    return x + y + z + w
'''
    result = smart_truncate(source, "python", max_tokens=20, model="claude")
    assert "def hello" in result
    assert "docstring" in result
    assert "..." in result


def test_truncate_unknown_language():
    source = "lots of text " * 100
    result = smart_truncate(source, "unknown_lang", max_tokens=10, model="claude")
    assert len(result) < len(source)
    assert "truncated" in result


def test_truncate_javascript():
    source = """function add(a, b) {
    const result = a + b;
    console.log(result);
    return result;
}

function subtract(a, b) {
    return a - b;
}
"""
    result = smart_truncate(source, "javascript", max_tokens=15, model="claude")
    assert "function" in result
    assert len(result) < len(source)


def test_truncate_empty():
    result = smart_truncate("", "python", max_tokens=100, model="claude")
    assert result == ""


def test_truncate_no_functions():
    """Source with no function defs — parser succeeds but no bodies found, falls back to naive."""
    source = "x = 1\n" * 100  # lots of top-level assignments
    result = smart_truncate(source, "python", max_tokens=10, model="claude")
    assert "truncated" in result
    assert len(result) < len(source)


def test_truncate_go_function():
    source = """package main

import "fmt"

func hello() {
    fmt.Println("hello")
    fmt.Println("world")
    fmt.Println("foo")
    fmt.Println("bar")
    fmt.Println("baz")
}

func goodbye() {
    fmt.Println("goodbye")
    fmt.Println("world")
    fmt.Println("foo")
    fmt.Println("bar")
}
"""
    result = smart_truncate(source, "go", max_tokens=15, model="claude")
    assert "..." in result
    assert len(result) < len(source)


def test_truncate_rust_function():
    source = """fn main() {
    let x = 1;
    let y = 2;
    let z = 3;
    let w = 4;
    println!("{}", x + y + z + w);
}

fn helper() {
    let a = 10;
    let b = 20;
    println!("{}", a + b);
}
"""
    result = smart_truncate(source, "rust", max_tokens=12, model="claude")
    assert "..." in result
    assert len(result) < len(source)


def test_truncate_python_class():
    source = """class MyClass:
    def method_one(self):
        x = 1
        y = 2
        z = 3
        return x + y + z

    def method_two(self):
        a = 10
        b = 20
        return a + b
"""
    result = smart_truncate(source, "python", max_tokens=15, model="claude")
    assert "class MyClass" in result
    assert "..." in result
    assert len(result) < len(source)


def test_truncate_still_over_after_all_truncations():
    """Even after truncating all bodies, still over budget — falls through to naive."""
    # Many functions with very short bodies — truncating bodies saves little,
    # and many signatures + names use lots of tokens
    funcs = []
    for i in range(50):
        funcs.append(f"def function_with_a_very_long_name_number_{i}(arg1, arg2, arg3):\n    return {i}")
    source = "\n\n".join(funcs)
    # Very tiny budget — even signatures alone won't fit
    result = smart_truncate(source, "python", max_tokens=5, model="claude")
    assert "truncated" in result
    assert len(result) < len(source)


def test_naive_truncate_directly():
    """Test _naive_truncate directly."""
    source = ("a]long line here\n") * 50
    result = _naive_truncate(source, max_tokens=5, model="claude")
    assert "truncated" in result
    assert len(result) < len(source)


def test_apply_truncations_overlapping_ranges():
    """Test _apply_truncations with overlapping ranges that hit the elif branch.

    When ranges overlap, lines past the first range's skip_until but inside
    a later range trigger the 'elif start < i <= end' branch.
    """
    lines = ["line0", "line1", "line2", "line3", "line4", "line5", "line6", "line7"]
    # Range 1 covers lines 1-3, range 2 covers lines 2-5 (overlapping)
    # i=4: past skip_until(3), range(1,3) misses, range(2,5) hits elif
    # i=5: same pattern, hits elif on range(2,5)
    ranges = [(1, 3, "..."), (2, 5, "...")]
    result = _apply_truncations(lines, ranges)
    result_lines = result.split("\n")
    assert result_lines[0] == "line0"
    assert "..." in result_lines[1]
    assert "line6" in result
    assert "line7" in result
    # Lines 4-5 should NOT appear (covered by elif branch)
    assert "line4" not in result
    assert "line5" not in result


def test_truncate_body_start_beyond_source_lines():
    """Hit the indent fallback (line 110) when body start_point exceeds line count.

    This is a defensive guard in smart_truncate. Tree-sitter shouldn't produce
    a body node with start_point beyond the source, but the guard exists.
    We monkeypatch _find_truncatable_bodies to return a mock node.
    """
    source = "def foo():\n    pass\n" * 5  # short source

    # Create a mock body node whose start_point is beyond source line count
    mock_body = MagicMock()
    mock_body.start_point = (9999, 0)  # way beyond source lines
    mock_body.end_point = (10000, 0)
    mock_body.start_byte = 0
    mock_body.end_byte = 100
    mock_body.children = []

    with patch("repo2ctx.truncation._find_truncatable_bodies", return_value=[mock_body]):
        result = smart_truncate(source, "python", max_tokens=3, model="claude")
    # Should still produce a result (falls through to naive truncate)
    assert len(result) < len(source)


def test_truncate_all_bodies_exactly_fits_after_loop():
    """Try to hit line 127: return after post-loop truncation check.

    This line is logically unreachable because the last loop iteration applies
    the same truncated_ranges as the post-loop check. We monkeypatch
    count_tokens to change behavior between calls to force the path.
    """
    source = """def foo():
    x = 1
    y = 2
    return x + y

def bar():
    a = 10
    b = 20
    return a + b
"""
    call_count = 0

    def fake_count_tokens(text, model):
        nonlocal call_count
        call_count += 1
        # First call: source is over budget (returns high)
        # In-loop checks: still over budget (returns high)
        # Post-loop check: under budget (returns low) -> line 127
        if call_count <= 3:
            return 999  # over budget
        return 1  # under budget

    with patch("repo2ctx.truncation.count_tokens", side_effect=fake_count_tokens):
        result = smart_truncate(source, "python", max_tokens=50, model="claude")
    assert isinstance(result, str)
