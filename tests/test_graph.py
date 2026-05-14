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


def test_topological_sort_with_cycle_remaining_nodes():
    """Create a cycle where Kahn's algorithm can't process some nodes.

    A->B->C->A forms a cycle. D is independent.
    Kahn's processes D first (in_degree=0), then the cycle nodes
    are appended in sorted order at the end.
    """
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")  # a imports b
    g.add_edge("b.py", "c.py")  # b imports c
    g.add_edge("c.py", "a.py")  # c imports a  (cycle!)
    g.add_node("d.py")          # independent node
    order = g.topological_sort()
    # d.py has in_degree=0, so it comes first
    assert order[0] == "d.py"
    # All cycle nodes should still appear
    assert set(order) == {"a.py", "b.py", "c.py", "d.py"}
    # The cycle nodes are appended in sorted order at the end
    cycle_nodes = order[1:]
    assert cycle_nodes == sorted(cycle_nodes)


def test_topological_sort_independent_nodes():
    """Multiple nodes with no edges should appear in sorted order."""
    g = DependencyGraph()
    g.add_node("c.py")
    g.add_node("a.py")
    g.add_node("b.py")
    order = g.topological_sort()
    assert order == ["a.py", "b.py", "c.py"]


def test_pagerank_disconnected_components():
    """Graph with disconnected components."""
    g = DependencyGraph()
    # Component 1
    g.add_edge("a.py", "b.py")
    # Component 2 (disconnected)
    g.add_edge("x.py", "y.py")
    scores = g.pagerank()
    assert len(scores) == 4
    # b and y are imported, should have higher scores than a and x
    assert scores["b.py"] > scores["a.py"]
    assert scores["y.py"] > scores["x.py"]


def test_reverse_edges_defensive_guard(monkeypatch):
    """Hit the defensive guard in reverse_edges where dep not in reverse dict.

    This guard is unreachable through the public API because self.nodes always
    includes all deps. We monkeypatch nodes to exclude a dep, forcing the guard.
    """
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")

    # Make nodes return only 'a.py', excluding 'b.py'
    # This forces the 'if dep not in reverse' guard to fire
    monkeypatch.setattr(
        type(g), "nodes", property(lambda self: {"a.py"})
    )
    rev = g.reverse_edges()
    # b.py should still end up in reverse via the guard
    assert "a.py" in rev["b.py"]


def test_topological_sort_dep_not_in_in_degree(monkeypatch):
    """Hit the defensive guard where dep not in in_degree dict.

    This guard is unreachable through the public API because all_nodes
    includes all deps. We monkeypatch nodes to exclude a dep, but the
    dep still appears in edges values so the inner loop's guard fires.
    """
    g = DependencyGraph()
    g.add_edge("a.py", "b.py")

    # Make nodes return only 'a.py', so b.py won't be in initial in_degree
    # but b.py still exists in edges["a.py"] = {"b.py"}
    monkeypatch.setattr(
        type(g), "nodes", property(lambda self: {"a.py"})
    )
    order = g.topological_sort()
    # Only a.py is in all_nodes, so only it appears in result
    assert "a.py" in order


def test_topological_sort_visited_continue_guard(monkeypatch):
    """Hit the 'if node in visited: continue' guard in topological_sort.

    This guard is a safety net that fires when a node appears in the queue
    twice. Normal in_degree accounting prevents this, so we monkeypatch
    deque to inject a duplicate entry.
    """
    from collections import deque as real_deque

    class DuplicatingDeque(real_deque):
        """A deque that duplicates the first appended item."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._injected = False

        def append(self, item):
            super().append(item)
            if not self._injected:
                super().append(item)  # duplicate!
                self._injected = True

    import repo2ctx.graph as graph_module
    original_deque = graph_module.deque
    monkeypatch.setattr(graph_module, "deque", DuplicatingDeque)

    g = DependencyGraph()
    g.add_edge("a.py", "b.py")
    order = g.topological_sort()
    # Should still produce correct results despite duplicate queue entry
    assert set(order) == {"a.py", "b.py"}
