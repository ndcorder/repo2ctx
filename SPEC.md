# repo2ctx — Project Specification

**23. repo2ctx**

*Intelligently prepare your codebase as LLM context --- not just a file
dump.*

  --------------------- -------------------------------------------------
  **Language**          Python 3.10+

  **Distribution**      PyPI (pip install repo2ctx)

  **Build Time**        5--7 days

  **License**           MIT

  **Category**          AI Tooling / Developer Productivity /
                        Language-Agnostic
  --------------------- -------------------------------------------------

**Problem**

Developers need to feed codebase context to LLMs for code review,
refactoring, and understanding. Existing tools (repomix, code2prompt,
aidigest) mostly do naive directory dumps, producing token-heavy context
that blows past LLM limits. They don't intelligently select relevant
files, count tokens accurately, or structure output for optimal LLM
comprehension.

**Solution**

A CLI that intelligently selects and formats codebase context for LLM
consumption. Uses dependency analysis, file importance scoring, and
configurable focus areas to produce optimized Markdown context that fits
within token budgets while maximizing information density.

**Core Features**

- **Intelligent file selection:** Scores files by import graph
  centrality, recent git activity, and configurable globs. Selects the
  most relevant files within a token budget.

- **Token-aware budgeting:** Accurate token counting (tiktoken for
  OpenAI, character-based for Claude). Respects a --max-tokens budget
  and reports utilization.

- **Dependency-aware ordering:** Orders files so that dependencies
  appear before dependents. LLMs process context better with bottom-up
  ordering.

- **Focus mode:** --focus path/to/file.py includes the target file plus
  all files it imports/is imported by, within the token budget.

- **Smart truncation:** When a file exceeds its budget share, truncates
  intelligently: keeps signatures, class/function headers, and
  docstrings; removes method bodies.

- **Output formats:** Markdown (default), XML tags (for Claude), and
  JSON. Includes file tree, file contents, and a summary preamble.

**Technical Architecture**

Python CLI using tree-sitter for multi-language parsing (Python, JS/TS,
Go, Rust, C#, PHP) to extract import graphs and structural elements. Git
log analysis provides recency scoring. Files are ranked by a weighted
score combining import centrality (PageRank-style), git recency, and
user-specified focus. The budget allocator distributes tokens
proportionally to scores. Smart truncation uses tree-sitter to identify
structural boundaries.

**CLI / API Surface**

> repo2ctx . # entire repo, default budget
>
> repo2ctx . --max-tokens 100000 # explicit budget
>
> repo2ctx . --focus src/auth/ # focus on auth module
>
> repo2ctx . --format xml # Claude-optimized format
>
> repo2ctx . --include '*.py' --exclude tests/ # filter
>
> cat output.md | pbcopy # pipe to clipboard

**Key Dependencies**

- tree-sitter + language grammars

- tiktoken

- gitpython

- typer

- rich

**Scope Boundaries**

**In scope:** Multi-language import analysis, token budgeting,
intelligent file selection, smart truncation, Markdown/XML/JSON output.

**Out of scope:** LLM API integration (this produces context, not sends
it). IDE plugins. Real-time file watching. Embedding generation.

**Success Criteria**

- Produces better LLM responses than naive dumps (measurable via blind
  comparison)

- Handles mono-repos with 10K+ files without OOM

- Token counts match actual model tokenizers within 2%