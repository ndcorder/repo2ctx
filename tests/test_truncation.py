"""Tests for smart truncation."""

from repo2ctx.truncation import smart_truncate


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
