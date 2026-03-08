# repo2ctx

**Intelligently prepare your codebase as LLM context — not just a file dump.**

repo2ctx analyzes your codebase and produces optimized context for LLM consumption. Unlike naive directory dumps, it uses dependency analysis, file importance scoring, and configurable focus areas to produce Markdown/XML/JSON context that fits within token budgets while maximizing information density.

## Features

- **Intelligent file selection** — Scores files by import graph centrality (PageRank), recent git activity, and configurable focus areas
- **Token-aware budgeting** — Accurate token counting via tiktoken (OpenAI) or character-based estimation (Claude), with configurable budget
- **Dependency-aware ordering** — Topological sort ensures dependencies appear before dependents for better LLM comprehension
- **Focus mode** — Zero in on specific files/directories plus their import neighbors
- **Smart truncation** — When files exceed their budget, preserves signatures, class headers, and docstrings while removing method bodies
- **Multi-language support** — tree-sitter parsing for Python, JavaScript, TypeScript, Go, and Rust
- **Multiple output formats** — Markdown (default), XML (Claude-optimized), and JSON

## Installation

```bash
pip install repo2ctx
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install repo2ctx
```

## Quick Start

```bash
# Analyze entire repo with default 128K token budget
repo2ctx .

# Set explicit token budget
repo2ctx . --max-tokens 100000

# Focus on a specific module
repo2ctx . --focus src/auth/

# Claude-optimized XML output
repo2ctx . --format xml

# Filter files
repo2ctx . --include '*.py' --exclude tests/

# Write to file
repo2ctx . --output context.md

# Use Claude token counting
repo2ctx . --model claude
```

## CLI Reference

```
repo2ctx PATH [OPTIONS]

Arguments:
  PATH                    Root directory to analyze

Options:
  -t, --max-tokens INT    Token budget (default: 128000)
  -f, --focus PATH        Focus on specific file/directory (repeatable)
  --format FORMAT         Output format: markdown, xml, json (default: markdown)
  -i, --include GLOB      Include only matching files (repeatable)
  -e, --exclude GLOB      Exclude matching files (repeatable)
  -m, --model MODEL       Token model: openai or claude (default: openai)
  -o, --output FILE       Write output to file instead of stdout
  --help                  Show help message
```

## How It Works

1. **Discovery** — Walks the directory tree, respecting `.gitignore`, skipping binary files and common non-code directories
2. **Import Analysis** — Uses tree-sitter to extract import graphs for supported languages
3. **Scoring** — Combines PageRank centrality (how many files import this?), git recency (recently modified = more relevant), and focus proximity
4. **Budget Allocation** — Distributes token budget proportionally to file scores
5. **Smart Truncation** — Files exceeding their allocation are truncated intelligently: signatures and docstrings are preserved, method bodies are replaced with `...`
6. **Output** — Formats everything as Markdown, XML, or JSON with file tree, summary stats, and ordered file contents

## Python API

```python
from pathlib import Path
from repo2ctx.pipeline import run

# Get context as a string
context = run(
    root=Path("."),
    max_tokens=100_000,
    focus=["src/auth/"],
    fmt="markdown",
    model="openai",
)
```

## Supported Languages

| Language | Import Extraction | Smart Truncation |
|-|-|-|
| Python | `import`, `from...import` | Functions, classes |
| JavaScript | `import`, `require()` | Functions, classes |
| TypeScript | `import`, `require()` | Functions, classes |
| Go | `import` | Functions |
| Rust | `use`, `extern crate` | Functions, impls |

Other file types are included but without import analysis or structural truncation.

## Development

```bash
# Clone and install
git clone https://github.com/your-org/repo2ctx.git
cd repo2ctx
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Format code
uv run ruff format .
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`uv run pytest`)
5. Ensure linting passes (`uv run ruff check .`)
6. Commit with descriptive messages (`feat: add my feature`)
7. Open a pull request

## License

MIT — see [LICENSE](LICENSE) for details.
