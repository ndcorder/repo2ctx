"""Tests for dependency graph."""

from repo2ctx.graph import DependencyGraph


def test_empty_graph():
    g = DependencyGraph()
    assert g.pagerank() == {}
    assert g.topological_sort() == []


def test_add_node():
    g = DependencyGraph()
    g.add_node("a.py")
    assert "a.py" in g.nodes


def test_add_edge():
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")
    assert "b.py" in g.edges["a.py"]
    assert "a.py" in g.nodes
    assert "b.py" in g.nodes


def test_pagerank_simple():
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")
    g.add_edge("c.py", "b.py")
    scores = g.pagerank()
    # b.py is imported by both a and c, should have highest score
    assert scores["b.py"] > scores["a.py"]
    assert scores["b.py"] > scores["c.py"]


def test_pagerank_chain():
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")
    g.add_edge("b.py", "c.py")
    scores = g.pagerank()
    # c is at the bottom, b imports c, a imports b
    assert scores["c.py"] > scores["b.py"]
    assert scores["b.py"] > scores["a.py"]


def test_topological_sort_linear():
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")  # a imports b
    g.add_edge("b.py", "c.py")  # b imports c
    order = g.topological_sort()
    assert order.index("c.py") < order.index("b.py")
    assert order.index("b.py") < order.index("a.py")


def test_topological_sort_diamond():
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")
    g.add_edge("a.py", "c.py")
    g.add_edge("b.py", "d.py")
    g.add_edge("c.py", "d.py")
    order = g.topological_sort()
    assert order.index("d.py") < order.index("b.py")
    assert order.index("d.py") < order.index("c.py")
    assert order.index("b.py") < order.index("a.py")
    assert order.index("c.py") < order.index("a.py")


def test_topological_sort_cycle():
    """Cycles should not cause infinite loop."""
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")
    g.add_edge("b.py", "a.py")
    order = g.topological_sort()
    assert set(order) == {"a.py", "b.py"}


def test_reverse_edges():
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")
    g.add_edge("a.py", "c.py")
    reverse = g.reverse_edges()
    assert "a.py" in reverse["b.py"]
    assert "a.py" in reverse["c.py"]


def test_neighbors():
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")
    g.add_edge("c.py", "a.py")
    neighbors = g.neighbors("a.py")
    assert "b.py" in neighbors  # a imports b
    assert "c.py" in neighbors  # c imports a


def test_single_node():
    g = DependencyGraph()
    g.add_node("alone.py")
    pr = g.pagerank()
    assert "alone.py" in pr
    assert pr["alone.py"] > 0
    assert g.topological_sort() == ["alone.py"]
