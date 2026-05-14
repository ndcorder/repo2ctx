# repo2ctx — Publishing & Promotion Plan

## One-Liner Pitch

> repo2ctx: Turn any codebase into token-optimized LLM context using PageRank, dependency analysis, and smart truncation.

## Competitive Landscape

Understand what exists so posts can position repo2ctx clearly.

| Tool | Stars | Language | Key Differentiator | Weakness repo2ctx exploits |
|-|-|-|-|-|
| [repomix](https://github.com/yamadashy/repomix) | ~22.6k | JS/TS | Packs entire repo into one AI-friendly file; Secretlint security scanning; tree-sitter compression | No PageRank/import-graph scoring; no intelligent budget allocation — it's "dump everything" not "pick what matters" |
| [gitingest](https://github.com/coderamp-labs/gitingest) | ~14.2k | Python | URL trick (`gitingest` instead of `github`); browser extensions; web UI | No dependency analysis, no smart truncation, no file importance scoring |
| [code2prompt](https://github.com/mufeedvh/code2prompt) | ~5.1k | Rust | TUI, Handlebars templates, git diff integration | No PageRank, no token-budget-proportional allocation, no structural truncation preserving signatures |
| [gpt-repository-loader](https://github.com/mpoon/gpt-repository-loader) | ~3k | Python | Simple, early mover (2023); `.gptignore` | Unmaintained feel (15 open PRs); no token counting, no import analysis, no truncation |

**Positioning angle for every post:** "These tools dump your repo. repo2ctx *scores* it — PageRank on the import graph, git recency, focus proximity — then allocates a token budget proportionally and uses structural truncation to preserve signatures while removing bodies. Same context window, dramatically better information density."

---

## 1. Package Registry Steps

### PyPI (primary)

1. Verify `pyproject.toml` metadata: `name`, `version`, `description`, `authors`, `license`, `urls`, `classifiers`, `keywords`
2. Add classifiers:
   ```
   "Development Status :: 4 - Beta",
   "Intended Audience :: Developers",
   "Topic :: Software Development :: Libraries",
   "Topic :: Scientific/Engineering :: Artificial Intelligence",
   "License :: OSI Approved :: MIT License",
   "Programming Language :: Python :: 3.10",
   "Programming Language :: Python :: 3.11",
   "Programming Language :: Python :: 3.12",
   "Programming Language :: Python :: 3.13",
   ```
3. Add keywords: `["llm", "context", "codebase", "token", "ai", "gpt", "claude", "tree-sitter", "pagerank", "code-to-prompt"]`
4. Build: `uv build`
5. Publish: `uv publish` (requires PyPI API token in `~/.pypirc` or `UV_PUBLISH_TOKEN`)
6. Verify: `pip install repo2ctx && repo2ctx --help`

### Conda-forge (secondary, post-launch)

1. Fork [conda-forge/staged-recipes](https://github.com/conda-forge/staged-recipes)
2. Add `recipes/repo2ctx/meta.yaml` with PyPI source
3. Open PR — conda-forge bot will review

---

## 2. GitHub SEO

### Repository Description

```
Turn any codebase into token-optimized LLM context. PageRank scoring, dependency-aware ordering, smart truncation.
```

### Topics (add via repo Settings > Topics)

`llm` · `context-window` · `codebase-analysis` · `token-budget` · `tree-sitter` · `pagerank` · `code-to-prompt` · `developer-tools` · `ai-tools` · `python`

### Additional GitHub SEO

- Social preview image (1280x640): before/after showing raw repo dump vs. repo2ctx scored + truncated output
- Pin the repo on your [GitHub profile](https://github.com/ndcorder)
- Add `FUNDING.yml` if you have a sponsor link

---

## 3. Reddit Posts

### Subreddit Rules Summary

| Subreddit | Members | Self-Promo Rules | Flair / Notes |
|-|-|-|-|
| [r/LocalLLaMA](https://reddit.com/r/LocalLLaMA) | ~700k | 10% rule (self-promo ≤10% of your activity) | Direct links, no clickbait titles |
| [r/ChatGPTCoding](https://reddit.com/r/ChatGPTCoding) | ~200k | Relaxed; project posts with demos welcome | Frequent project shares succeed |
| [r/Python](https://reddit.com/r/Python) | ~1.3M | Welcoming to quality project posts | Use "Showcase" flair; include what-it-does, what-you-learned, comparison |
| [r/CommandLine](https://reddit.com/r/commandline) | ~200k | Standard Reddit rules; be a member first | Technical focus; show CLI output |
| [r/MachineLearning](https://reddit.com/r/MachineLearning) | ~3M | Use monthly "What are you working on?" thread | No standalone project posts outside the thread |

### Draft 1 — r/LocalLLaMA

**Title:** `I built repo2ctx — it uses PageRank on your import graph to pick the most important files for your LLM context window`

**Body:**

```
I was frustrated with how much context window gets wasted when feeding code to
LLMs. Tools like repomix and gitingest dump your entire repo, but not all files
matter equally.

repo2ctx builds an import graph using tree-sitter, runs PageRank to find the
most central files, factors in git recency, and allocates your token budget
proportionally. When a file exceeds its allocation, it uses structural
truncation — preserving function signatures and docstrings while removing
method bodies.

Quick comparison on a real 500-file Python project:
- repomix: 180K tokens, no prioritization
- repo2ctx with 100K budget: top-scored files fully included, less important
  files intelligently truncated, signatures preserved everywhere

Supports Python, JS/TS, Go, Rust. Output in Markdown, XML (Claude-optimized),
or JSON.

    pip install repo2ctx
    repo2ctx . --max-tokens 100000

GitHub: https://github.com/ndcorder/repo2ctx

MIT licensed. Would love feedback on the scoring heuristics and what languages
to prioritize next.
```

### Draft 2 — r/ChatGPTCoding

**Title:** `Stop pasting random files into ChatGPT. repo2ctx scores your code by importance and fits it into your token budget.`

**Body:**

```
I built a CLI that analyzes your codebase and picks the files that matter most
for your LLM conversation. Instead of manually selecting files or dumping
everything, it:

1. Builds an import graph (which files depend on which?)
2. Runs PageRank to find central files
3. Allocates your token budget proportionally to importance scores
4. Truncates overflow files intelligently — keeps signatures, removes bodies

Real workflow: point it at your project, pipe to clipboard, paste into ChatGPT/
Claude. You get better answers because the LLM sees the most important code
first.

    pip install repo2ctx
    repo2ctx . --max-tokens 100000 --focus src/auth/ | pbcopy

Works with Python, JavaScript, TypeScript, Go, Rust.

GitHub: https://github.com/ndcorder/repo2ctx
```

### Draft 3 — r/Python

**Title:** `repo2ctx: Python CLI using tree-sitter + PageRank to prepare your codebase as LLM context`

**Body:**

```
Sharing a tool I built for preparing codebases as LLM context.

**What My Project Does**

repo2ctx analyzes your codebase and produces token-optimized context for LLM
consumption. It extracts import graphs using tree-sitter, runs PageRank to score
file importance, factors in git recency, and allocates a token budget
proportionally. Files exceeding their allocation are structurally truncated —
function signatures and docstrings are preserved, method bodies are replaced
with `...`.

**Target Audience**

Developers who use LLMs (ChatGPT, Claude, etc.) for code understanding, review,
or generation and want better results from the same context window.

**Comparison**

Unlike repomix (22.6k stars, JS) and gitingest (14.2k stars, Python) which dump
all files without prioritization, repo2ctx scores files by import-graph
centrality and allocates tokens proportionally. Unlike code2prompt (5.1k stars,
Rust) which offers templates but no dependency-aware scoring, repo2ctx uses
PageRank on the actual import graph.

**Technical highlights:**
- tree-sitter parsing for Python, JS/TS, Go, Rust
- tiktoken (OpenAI) or char-based (Claude) token counting
- Topological sort so dependencies appear before dependents
- Focus mode: zoom into a module + its import neighborhood
- Markdown, XML (Claude-optimized), JSON output

    pip install repo2ctx
    # or: uv tool install repo2ctx

GitHub: https://github.com/ndcorder/repo2ctx
MIT license.
```

### Draft 4 — r/CommandLine

**Title:** `repo2ctx — CLI that uses PageRank to pick the most important files from your codebase for LLM context`

**Body:**

```
    # Analyze repo with 100K token budget
    repo2ctx . --max-tokens 100000

    # Focus on auth module + its dependencies
    repo2ctx . --focus src/auth/ --format xml

    # Filter to Python files only
    repo2ctx . --include '*.py' --exclude tests/

Built with Typer. Supports Markdown, XML, JSON output. Uses tree-sitter for
import extraction and PageRank for file scoring.

pip install repo2ctx

https://github.com/ndcorder/repo2ctx
```

---

## 4. Hacker News

### Show HN Title

```
Show HN: repo2ctx – Turn any codebase into token-optimized LLM context
```

### Founder Comment (post immediately after submission)

```
Hi HN — I built repo2ctx because I was frustrated with how much context window
gets wasted when feeding code to LLMs.

Existing tools (repomix, gitingest, code2prompt) dump your repo into a single
file, but treat all files as equally important. In reality, a core module
imported by 30 files carries far more information than a test fixture.

repo2ctx builds an import graph from your codebase using tree-sitter, runs
PageRank to find the most central files, factors in git recency, and allocates
your token budget proportionally to these combined scores.

When a file exceeds its allocation, it uses structural truncation — preserving
function signatures and docstrings while removing method bodies. The result is
dramatically more useful context for the same token count.

Supports Python, JS/TS, Go, and Rust. Output in Markdown, XML
(Claude-optimized), or JSON.

    pip install repo2ctx
    repo2ctx . --max-tokens 100000

Would love feedback — especially on whether the scoring heuristics match your
intuitions about file importance, and what languages to prioritize next.

GitHub: https://github.com/ndcorder/repo2ctx
```

### HN Timing

Post Tuesday–Thursday between 8–10 AM ET for best visibility. Avoid Mondays (backlog competition) and Fridays (lower engagement).

---

## 5. Dev.to Article

### Title

```
How I Used PageRank to Solve the LLM Context Window Problem
```

### Outline

1. **The Problem** — LLMs have limited context windows; blindly pasting files wastes tokens on test fixtures and boilerplate
2. **What Existing Tools Do** — repomix, gitingest, code2prompt all dump files; none score importance
3. **The Insight** — Codebases have structure; files imported by many others carry more information
4. **Building the Import Graph** — How tree-sitter extracts imports across 5 languages
5. **PageRank for Code** — Applying Google's algorithm to find the "most important" source files
6. **Token Budget Allocation** — Proportional distribution based on combined scores (PageRank + git recency + focus proximity)
7. **Smart Truncation** — Preserving signatures while removing bodies (with before/after code examples)
8. **Focus Mode** — Zooming in on a module and its dependency neighborhood
9. **Results** — Before/after comparison on a real open-source repo (token counts, information density)
10. **Try It** — `pip install repo2ctx`, basic usage, link to GitHub

### Tags

`#python` `#ai` `#productivity` `#opensource`

### Cross-post to

- [Hashnode](https://hashnode.com/) — strong developer audience, supports canonical URLs
- Personal blog (if any) — canonical source

---

## 6. Awesome-List PRs

### Verified Lists (active, accepting PRs as of March 2026)

| Awesome List | Stars | Section to Target | Status | PR Format |
|-|-|-|-|-|
| [awesome-python](https://github.com/vinta/awesome-python) | ~272k | Code Analysis | Active. Strict: 1 project per PR, alpha order, automated quality checks. Wait until 100+ stars. | `- [repo2ctx](https://github.com/ndcorder/repo2ctx) - Prepare codebases as token-optimized LLM context using PageRank and dependency analysis.` |
| [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) | ~88k | Follow existing structure; include a demo app + README | Active. Accepts PRs with full app implementations, not just links. | Submit a working example app using repo2ctx with a README |
| [awesome-cli-apps](https://github.com/agarrharr/awesome-cli-apps) | ~19k | Development > Code Analysis (or new "AI" subsection) | Active, ~15k stars, PRs reviewed regularly | `- [repo2ctx](https://github.com/ndcorder/repo2ctx) - Prepare codebases as token-optimized LLM context using import graph analysis.` |

### Dead / Unsuitable Lists (removed from plan)

| List | Reason |
|-|-|
| ~~sourcegraph/awesome-code-ai~~ | **Archived** February 2026. Read-only, no new PRs accepted. |
| ~~farzad-845/awesome-generative-ai-tools~~ | **404 — repo does not exist** (possibly deleted or renamed). |
| ~~saharmor/awesome-chatgpt~~ | **Stale** — last updated June 2023, only 582 stars. Not worth the PR. |

### Additional Awesome Lists to Target

| Awesome List | Stars | Why |
|-|-|-|
| [awesome-llm-agents](https://github.com/kaushikb11/awesome-llm-agents) | Growing | LLM agent frameworks list; repo2ctx fits as a context-preparation tool |
| [awesome-code-ai](https://github.com/ai-for-developers/awesome-ai-coding-tools) | Replacement for archived Sourcegraph list | Curated AI-powered coding tools |
| [awesome-llm-webapps](https://github.com/icefort-ai/awesome-llm-webapps) | Active | If you build a web UI for repo2ctx |

### PR Tips

- Read each repo's CONTRIBUTING.md before submitting
- One PR per list, spaced 1–2 days apart
- For awesome-python: ensure your PyPI package has downloads, tests pass, and the project is non-trivial
- For awesome-llm-apps: they want full working app directories with READMEs, not just links

---

## 7. Newsletters & Communities

### Newsletters (submit or pitch)

| Newsletter | Audience | How to Submit | URL |
|-|-|-|-|
| **TLDR** | 1M+ devs, daily | Pitch via their contact form; they curate Show HN / trending GitHub | https://tldr.tech/ |
| **TLDR AI** | AI-focused subset of TLDR | Same pipeline — AI tools get picked up from HN/GitHub trending | https://tldr.tech/ai |
| **Python Weekly** | Python devs, weekly | Submit via GitHub issue on their repo | https://www.pythonweekly.com/ |
| **PyCoder's Weekly** | Python devs, weekly | Submit link via their site | https://pycoders.com/ |
| **Console.dev** | CTOs, senior devs, weekly | They discover tools organically; 68% of readers sign up to featured tools. Not accepting direct submissions for editorial — only paid sponsorships. | https://console.dev/ |
| **The Rundown AI** | 1.75M readers, daily | Pitch via contact; they pick trending AI tools | https://www.therundown.ai/ |

### Communities (post or share)

| Community | How to Engage | URL |
|-|-|-|
| **Hacker News** | Show HN post (see Section 4) | https://news.ycombinator.com/ |
| **Lobsters** | Invite-only. Get an invite from an existing member, then submit under `ai` and `python` tags | https://lobste.rs/ |
| **Dev.to** | Publish article (see Section 5) | https://dev.to/ |
| **Indie Hackers** | "Show IH" post; share the build story, not just the product | https://www.indiehackers.com/ |
| **X / Twitter** | Post with GIF demo, tag @ClaudeAI @OpenAI; use hashtags #DevTools #LLM #OpenSource | https://x.com/ |
| **LinkedIn** | Short "why I built this" story targeting engineering managers | https://linkedin.com/ |
| **LLM Discord servers** | Share in #tools or #projects channels on LocalLLaMA Discord, Nous Research, etc. | Search "LocalLLaMA Discord" |

---

## 8. Directories & Launch Platforms

| Platform | Category | Cost | Action | URL |
|-|-|-|-|-|
| **Product Hunt** | Dev Tools | Free | Prepare 5 screenshots, tagline, maker comment. Launch on a Tuesday. | https://www.producthunt.com/ |
| **DevHunt** | Dev Tools | Free | Dev-focused PH alternative; GitHub auth ensures real votes. Less competition. | https://devhunt.org/ |
| **MicroLaunch** | Startups | Free | Month-long ranking cycle; good for sustained visibility. | https://microlaunch.net/ |
| **AlternativeTo** | Code Analysis | Free | List as alternative to "repomix", "code2prompt", "gitingest", "gpt-repository-loader". Sign up, click "Suggest new application". | https://alternativeto.net/ |
| **There's An AI For That** | Code Analysis | $347 (one-off, refunded if rejected) | Submit under "Code Analysis" or "Developer Tools". 1–2 day review. Monthly free thread on X for indie makers. | https://theresanaiforthat.com/submit/ |
| **Toolify.ai** | AI Developer Tools | $49–99 | Submit at their form. Listed within 48 hours. | https://www.toolify.ai/submit |
| **Libraries.io** | Auto-indexed | Free | Auto-indexed from PyPI — verify listing after publish | https://libraries.io/ |

---

## 9. Day 0–7 Launch Timeline

### Day 0 (Prep — do everything before launch day)

- [ ] Final README polish — add badges (PyPI version, downloads, license, Python versions)
- [ ] Record a 30-second terminal GIF using [vhs](https://github.com/charmbracelet/vhs) or [asciinema](https://asciinema.org/)
- [ ] Prepare social preview image (1280x640) for GitHub
- [ ] Write all post drafts (finalize from Section 3–5 above)
- [ ] Publish to PyPI: `uv build && uv publish`
- [ ] Verify: `pip install repo2ctx && repo2ctx --help`
- [ ] Set GitHub repo description and topics (Section 2)
- [ ] Submit to AlternativeTo (takes time to approve)

### Day 1 (Tuesday or Wednesday — Launch Day)

- [ ] 9 AM ET: Post Show HN, immediately add founder comment
- [ ] Post to r/LocalLLaMA (Draft 1)
- [ ] Tweet/post on X with GIF — tag @ClaudeAI, @OpenAI
- [ ] Post on LinkedIn with "why I built this" narrative
- [ ] Submit to DevHunt

### Day 2

- [ ] Post to r/ChatGPTCoding (Draft 2)
- [ ] Submit first awesome-list PR (awesome-cli-apps — fastest turnaround)
- [ ] Respond to ALL HN and Reddit comments (engagement drives ranking)
- [ ] Submit to MicroLaunch

### Day 3

- [ ] Post to r/Python (Draft 3 — use "Showcase" flair)
- [ ] Publish Dev.to article
- [ ] Submit second awesome-list PR (awesome-python if >100 stars, otherwise awesome-llm-agents)
- [ ] Cross-post article to Hashnode

### Day 4

- [ ] Submit to Product Hunt (prepare night before: screenshots, tagline, first comment)
- [ ] Submit to Toolify.ai
- [ ] Post to r/CommandLine (Draft 4)
- [ ] Submit third awesome-list PR

### Day 5

- [ ] Pitch Python Weekly and PyCoder's Weekly (email/issue with GitHub link + PyPI link)
- [ ] Post in r/MachineLearning "What are you working on?" thread (if one is active)
- [ ] Submit to There's An AI For That (if budget allows $347; otherwise wait for free X thread)

### Day 6

- [ ] Write a follow-up post addressing top feedback/questions from launch
- [ ] Open GitHub issues for feature requests that came from comments
- [ ] Thank contributors and commenters publicly
- [ ] Share "Day 1–5 results" post on Indie Hackers

### Day 7

- [ ] Review analytics: PyPI downloads (`pip-download-stats`), GitHub stars, traffic sources (repo Insights > Traffic)
- [ ] Identify top referral source — double down on what worked
- [ ] Plan v1.1.0 based on launch feedback
- [ ] Start conda-forge recipe if demand exists
- [ ] If Show HN or Reddit posts got traction, write a "Lessons from launching repo2ctx" Dev.to article (great for sustained traffic)
