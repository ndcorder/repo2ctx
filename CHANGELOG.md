# Changelog

All notable changes to repo2ctx will be documented in this file.

## [0.1.0] - 2026-03-07

Initial release of repo2ctx — intelligent codebase context for LLMs.

### New Features

- **Intelligent file selection** — Scores files by import graph centrality (PageRank), recent git activity, and configurable focus areas to surface the most relevant code within your token budget.

- **Token-aware budgeting** — Accurate token counting using tiktoken (OpenAI) or character-based estimation (Claude). Set a `--max-tokens` budget and repo2ctx distributes it proportionally across files by importance.

- **Dependency-aware ordering** — Topological sort ensures dependencies appear before the files that import them, so LLMs see foundational code first.

- **Focus mode** — Use `--focus src/auth/` to zero in on a specific file or directory, automatically including its import neighbors within the token budget.

- **Smart truncation** — When files exceed their allocation, tree-sitter-powered truncation preserves class/function signatures, docstrings, and type definitions while removing method bodies.

- **Multi-language support** — Tree-sitter import extraction and structural parsing for Python, JavaScript, TypeScript, Go, and Rust.

- **Multiple output formats** — Markdown (default), XML (optimized for Claude), and JSON. Each includes a file tree, summary statistics, and ordered file contents.

- **CLI with all the knobs** — `repo2ctx PATH` with options for `--max-tokens`, `--focus`, `--format`, `--include`, `--exclude`, `--model`, and `--output`.

### Performance & Reliability

- Cached tiktoken encoding — loaded once, reused across all token counts.
- Batched git log queries — single subprocess call instead of one per file.
- O(1) deque-based topological sort instead of O(n) list pops.
- XML output properly escapes `<`, `>`, `&`, and `"` in file paths and content.
- `.egg-info` and other glob-patterned directories correctly skipped during discovery.
- Dynamic minimum token allocation prevents small budgets from being overrun.

### Developer Experience

- 93 tests with 88% code coverage across all modules.
- Ruff linting and formatting enforced.
- GitHub Actions CI testing Python 3.10–3.13.
- Installable via `pip install repo2ctx` or `uv tool install repo2ctx`.
