"""Tests for output formatting."""

import json

from repo2ctx.budget import BudgetAllocation
from repo2ctx.formats import format_output


def _make_allocations():
    return [
        BudgetAllocation(
            file_path="src/main.py",
            allocated_tokens=100,
            actual_tokens=50,
            content="print('hello')",
            truncated=False,
        ),
        BudgetAllocation(
            file_path="src/utils.py",
            allocated_tokens=80,
            actual_tokens=80,
            content="def add(a, b): ...",
            truncated=True,
        ),
    ]


def test_markdown_format():
    allocs = _make_allocations()
    result = format_output(allocs, "├── src\n│   ├── main.py", fmt="markdown")
    assert "# Repository Context" in result
    assert "```python" in result
    assert "src/main.py" in result
    assert "(truncated)" in result


def test_markdown_with_stats():
    allocs = _make_allocations()
    stats = {"Total files": 2, "Total tokens": 130}
    result = format_output(allocs, "", fmt="markdown", stats=stats)
    assert "**Total files**: 2" in result


def test_xml_format():
    allocs = _make_allocations()
    result = format_output(allocs, "tree", fmt="xml")
    assert "<repository-context>" in result
    assert '<file path="src/main.py">' in result
    assert 'truncated="true"' in result
    assert "</repository-context>" in result


def test_xml_with_stats():
    allocs = _make_allocations()
    stats = {"Total files": 2}
    result = format_output(allocs, "", fmt="xml", stats=stats)
    assert "<summary>" in result
    assert "<total-files>2</total-files>" in result


def test_json_format():
    allocs = _make_allocations()
    result = format_output(allocs, "tree", fmt="json")
    data = json.loads(result)
    assert "files" in data
    assert len(data["files"]) == 2
    assert data["files"][0]["path"] == "src/main.py"
    assert data["files"][1]["truncated"] is True
    assert data["file_tree"] == "tree"


def test_json_with_stats():
    allocs = _make_allocations()
    stats = {"Total files": 2}
    result = format_output(allocs, "", fmt="json", stats=stats)
    data = json.loads(result)
    assert data["summary"]["Total files"] == 2


def test_empty_allocations():
    result = format_output([], "", fmt="markdown")
    assert "# Repository Context" in result


def test_format_default_is_markdown():
    allocs = _make_allocations()
    result = format_output(allocs, "")
    assert "# Repository Context" in result


def test_xml_escapes_special_chars():
    allocs = [
        BudgetAllocation(
            file_path='src/a<b>.py',
            allocated_tokens=100,
            actual_tokens=50,
            content='x = "a & b < c"',
            truncated=False,
        ),
    ]
    result = format_output(allocs, "", fmt="xml")
    assert "&lt;b&gt;" in result
    assert "&amp;" in result
    assert "</file>" in result  # structure intact
