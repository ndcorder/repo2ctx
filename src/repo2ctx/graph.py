"""Dependency graph with PageRank scoring and topological sort."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    """Directed graph of file dependencies."""

    # file -> set of files it imports (outgoing edges)
    edges: dict[str, set[str]] = field(default_factory=dict)

    def add_node(self, node: str) -> None:
        if node not in self.edges:
            self.edges[node] = set()

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add edge: from_node imports to_node."""
        self.add_node(from_node)
        self.add_node(to_node)
        self.edges[from_node].add(to_node)

    @property
    def nodes(self) -> set[str]:
        result = set(self.edges.keys())
        for deps in self.edges.values():
            result.update(deps)
        return result

    def reverse_edges(self) -> dict[str, set[str]]:
        """Get reverse graph (dependents -> dependencies)."""
        reverse: dict[str, set[str]] = {n: set() for n in self.nodes}
        for node, deps in self.edges.items():
            for dep in deps:
                if dep not in reverse:
                    reverse[dep] = set()
                reverse[dep].add(node)
        return reverse

    def neighbors(self, node: str) -> set[str]:
        """Get all neighbors (imports + imported-by) of a node."""
        result = set(self.edges.get(node, set()))
        for n, deps in self.edges.items():
            if node in deps:
                result.add(n)
        return result

    def pagerank(self, damping: float = 0.85, iterations: int = 100) -> dict[str, float]:
        """Compute PageRank scores for all nodes.

        Uses the reverse graph: a file that is imported by many files gets a high score.
        """
        all_nodes = list(self.nodes)
        n = len(all_nodes)
        if n == 0:
            return {}

        # Initialize scores uniformly
        scores = {node: 1.0 / n for node in all_nodes}

        # Build reverse adjacency (who imports this file?)
        reverse = self.reverse_edges()

        for _ in range(iterations):
            new_scores: dict[str, float] = {}
            for node in all_nodes:
                rank_sum = 0.0
                for referrer in reverse.get(node, set()):
                    out_degree = len(self.edges.get(referrer, set()))
                    if out_degree > 0:
                        rank_sum += scores[referrer] / out_degree
                new_scores[node] = (1 - damping) / n + damping * rank_sum
            scores = new_scores

        return scores

    def topological_sort(self) -> list[str]:
        """Topological sort: dependencies before dependents.

        Uses Kahn's algorithm. edges[A] = {B} means A imports B,
        so B must come before A. In-degree counts how many imports
        each node has (i.e., how many things it depends on).

        If there are cycles, remaining nodes are appended in sorted order.
        """
        all_nodes = self.nodes
        in_degree: dict[str, int] = {n: 0 for n in all_nodes}
        for node, deps in self.edges.items():
            in_degree[node] = in_degree.get(node, 0) + len(deps)
            for dep in deps:
                if dep not in in_degree:
                    in_degree[dep] = 0

        queue = deque(n for n in sorted(all_nodes) if in_degree.get(n, 0) == 0)
        result: list[str] = []
        visited: set[str] = set()

        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            result.append(node)

            # Find all nodes that import this node — they can now be processed
            for other, deps in self.edges.items():
                if node in deps and other not in visited:
                    in_degree[other] -= 1
                    if in_degree[other] <= 0:
                        queue.append(other)

        # Append remaining nodes (cycles) in sorted order
        for node in sorted(all_nodes):
            if node not in visited:
                result.append(node)

        return result
