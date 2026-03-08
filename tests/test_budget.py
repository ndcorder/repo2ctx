"""Tests for budget allocation."""

from repo2ctx.budget import BudgetAllocation, allocate_budget


def test_allocate_within_budget():
    files = {"a.py": "print('hello')", "b.py": "x = 1"}
    scores = {"a.py": 0.8, "b.py": 0.2}
    result = allocate_budget(files, scores, max_tokens=10000, model="openai")
    assert len(result) == 2
    assert all(not a.truncated for a in result)


def test_allocate_empty():
    result = allocate_budget({}, {}, max_tokens=1000)
    assert result == []


def test_allocate_respects_scores():
    content_a = "x = 1\n" * 200
    content_b = "y = 2\n" * 200
    files = {"a.py": content_a, "b.py": content_b}
    scores = {"a.py": 0.9, "b.py": 0.1}
    # Budget smaller than total content to trigger proportional allocation
    result = allocate_budget(files, scores, max_tokens=200, model="claude")
    alloc_a = next(a for a in result if a.file_path == "a.py")
    alloc_b = next(a for a in result if a.file_path == "b.py")
    assert alloc_a.allocated_tokens > alloc_b.allocated_tokens


def test_allocate_truncates_large_files():
    big_content = "def foo():\n    return 'bar'\n" * 500
    small_content = "x = 1"
    files = {"big.py": big_content, "small.py": small_content}
    scores = {"big.py": 0.5, "small.py": 0.5}
    result = allocate_budget(files, scores, max_tokens=100, model="claude")
    big_alloc = next(a for a in result if a.file_path == "big.py")
    assert big_alloc.truncated


def test_budget_allocation_dataclass():
    a = BudgetAllocation(
        file_path="test.py",
        allocated_tokens=100,
        actual_tokens=50,
        content="pass",
        truncated=False,
    )
    assert a.file_path == "test.py"
    assert a.allocated_tokens == 100
