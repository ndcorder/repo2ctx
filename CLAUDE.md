# repo2ctx Project Conventions

## Code Style
- Python 3.10+ — use `match`, `|` union types, modern syntax
- Ruff for linting and formatting (line-length=100)
- Type hints on all public functions
- No docstrings on obvious methods; docstrings on complex logic only

## Project Structure
- Source in `src/repo2ctx/`
- Tests in `tests/`
- Entry point: `repo2ctx.cli:app` (Typer)

## Commit Format
- `feat:` new features
- `fix:` bug fixes
- `test:` test additions/changes
- `docs:` documentation
- `refactor:` code changes that don't add features or fix bugs
- `chore:` maintenance tasks

## Test Patterns
- pytest, files named `test_*.py`
- Use tmp_path fixture for filesystem tests
- Use monkeypatch for git/external dependencies
- Test edge cases: empty repos, binary files, missing .git

## Architecture
- `discovery.py` — file walking, gitignore, include/exclude filtering
- `imports.py` — tree-sitter import extraction per language
- `graph.py` — dependency graph, PageRank scoring, topological sort
- `scoring.py` — combined scoring (imports + git recency + focus)
- `tokens.py` — token counting (tiktoken / char-based)
- `budget.py` — token budget allocation across files
- `truncation.py` — smart truncation preserving signatures
- `formats.py` — output formatting (markdown, xml, json)
- `cli.py` — Typer CLI
