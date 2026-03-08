# repo2ctx Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI that intelligently selects and formats codebase context for LLM consumption.

**Architecture:** File discovery → import graph extraction → scoring → budget allocation → smart truncation → formatted output. Each stage is a separate module with clear interfaces. The CLI orchestrates the pipeline.

**Tech Stack:** Python 3.10+, tree-sitter (multi-lang parsing), tiktoken (token counting), gitpython (git analysis), typer (CLI), rich (terminal output)

---

## Critical Path

1. Token counting (foundation for budget)
2. File discovery (need files before anything else)
3. Import extraction (tree-sitter per language)
4. Dependency graph (PageRank, topological sort)
5. Git recency scoring
6. Combined scoring + budget allocation
7. Smart truncation
8. Output formatting
9. CLI integration

## Task 1: Token Counting (`tokens.py`)

**Files:** `src/repo2ctx/tokens.py`, `tests/test_tokens.py`

Two counting strategies:
- `tiktoken` for OpenAI models (cl100k_base encoding)
- Character-based for Claude (~4 chars per token)

Interface:
```python
def count_tokens(text: str, model: str = "openai") -> int
```

## Task 2: File Discovery (`discovery.py`)

**Files:** `src/repo2ctx/discovery.py`, `tests/test_discovery.py`

Walk directory, respect .gitignore via gitpython, apply --include/--exclude glob filters.
Skip binary files, hidden dirs (except .github), and common non-code dirs (node_modules, .git, __pycache__, .venv).

Interface:
```python
@dataclass
class FileInfo:
    path: Path
    relative_path: str
    size: int
    extension: str

def discover_files(
    root: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[FileInfo]
```

## Task 3: Import Extraction (`imports.py`)

**Files:** `src/repo2ctx/imports.py`, `tests/test_imports.py`

Use tree-sitter to extract imports for each language:
- Python: `import X`, `from X import Y`
- JavaScript/TypeScript: `import ... from 'X'`, `require('X')`
- Go: `import "X"`, `import ( "X" )`
- Rust: `use X`, `mod X`, `extern crate X`

Interface:
```python
def extract_imports(source: bytes, language: str) -> list[str]
def detect_language(path: Path) -> str | None
```

## Task 4: Dependency Graph (`graph.py`)

**Files:** `src/repo2ctx/graph.py`, `tests/test_graph.py`

Build a directed graph from imports. Compute:
- PageRank-style centrality scores
- Topological sort for dependency-aware ordering

Interface:
```python
@dataclass
class DependencyGraph:
    nodes: dict[str, set[str]]  # file -> set of files it imports

    def pagerank(self, damping: float = 0.85, iterations: int = 100) -> dict[str, float]
    def topological_sort(self) -> list[str]
```

## Task 5: Git Recency Scoring (`scoring.py`)

**Files:** `src/repo2ctx/scoring.py`, `tests/test_scoring.py`

Use gitpython to get last-modified timestamps. Score by recency (exponential decay).
Combine with PageRank and focus proximity for final scores.

Interface:
```python
def git_recency_scores(root: Path, files: list[str]) -> dict[str, float]
def compute_scores(
    files: list[str],
    graph: DependencyGraph,
    root: Path,
    focus: list[str] | None = None,
) -> dict[str, float]
```

## Task 6: Budget Allocation (`budget.py`)

**Files:** `src/repo2ctx/budget.py`, `tests/test_budget.py`

Distribute token budget proportionally to file scores.
Each file gets `(score / total_score) * budget` tokens.

Interface:
```python
@dataclass
class BudgetAllocation:
    file_path: str
    allocated_tokens: int
    actual_tokens: int
    content: str
    truncated: bool

def allocate_budget(
    files: dict[str, str],  # path -> content
    scores: dict[str, float],
    max_tokens: int,
    model: str = "openai",
) -> list[BudgetAllocation]
```

## Task 7: Smart Truncation (`truncation.py`)

**Files:** `src/repo2ctx/truncation.py`, `tests/test_truncation.py`

When a file exceeds its budget, truncate intelligently:
- Keep class/function signatures and docstrings
- Remove method bodies (replace with `...`)
- Use tree-sitter to find structural boundaries

Interface:
```python
def smart_truncate(source: str, language: str, max_tokens: int, model: str = "openai") -> str
```

## Task 8: Output Formatting (`formats.py`)

**Files:** `src/repo2ctx/formats.py`, `tests/test_formats.py`

Three output formats:
- **Markdown** (default): File tree + fenced code blocks
- **XML**: `<file path="...">` tags (Claude-optimized)
- **JSON**: Structured object

Interface:
```python
def format_output(
    allocations: list[BudgetAllocation],
    file_tree: str,
    format: str = "markdown",
    stats: dict | None = None,
) -> str
```

## Task 9: CLI (`cli.py`)

**Files:** `src/repo2ctx/cli.py`, `tests/test_cli.py`

Typer CLI with commands:
```
repo2ctx PATH [OPTIONS]
  --max-tokens INT     Token budget (default: 128000)
  --focus PATH         Focus on specific file/directory
  --format FORMAT      Output format: markdown|xml|json
  --include GLOB       Include only matching files (repeatable)
  --exclude GLOB       Exclude matching files (repeatable)
  --model MODEL        Token model: openai|claude (default: openai)
  --output FILE        Write to file instead of stdout
```

## Task 10: Pipeline Integration

**Files:** `src/repo2ctx/pipeline.py`

Wire everything together in a clean pipeline function that the CLI calls.

## Architectural Decisions

1. **No C# / PHP tree-sitter**: Spec mentions them but reliable Python bindings aren't in PyPI. Will use regex fallback for unsupported languages.
2. **PageRank implementation**: Simple iterative approach, no numpy dependency.
3. **Gitignore**: Use gitpython's `ignored()` check rather than reimplementing.
4. **Default token budget**: 128K tokens (GPT-4 context window).
5. **Focus mode**: Files within focus path + their direct import neighbors get score multiplier.
