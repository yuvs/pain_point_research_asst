# Pain Point Research Assistant — Claude Code Project

A multi-agent Claude Code system that researches online communities for business pain points, synthesizes findings into prioritized reports, and maps the competitive landscape of solution providers.

## What This Does

Running a consulting business means finding problems worth solving — but manually sifting through Reddit threads, LinkedIn posts, and Quora answers to spot recurring frustrations is time-consuming and easy to get wrong. This tool automates that research loop end-to-end.

Point it at any industry or role (e.g. "e-commerce operators", "restaurant owners", "HR managers at mid-size companies") and it will:

1. **Scrape four platforms** — Reddit, LinkedIn, X/Twitter, and Quora — for posts where business owners express genuine frustrations, challenges, or unmet needs.
2. **Deduplicate and categorize** findings across operations, finance, hiring, technology, compliance, marketing, and more.
3. **Prioritize using ICE + WTP** — each pain point is scored on Impact, Confidence, and Ease of addressing, then weighted by how explicitly people mention budget or willingness to spend. This surfaces the problems most worth building a consulting offering around.
4. **Map the competitive landscape** — for the top-ranked pain points, it finds existing solution providers, profiles their pricing and positioning, and identifies gaps you can move into.
5. **Produce a dated markdown report** in `reports/` ready to share with a client or use as a strategy brief.

The result is a research brief that would otherwise take a junior analyst several days to compile — delivered in one command.

## Setup

### Prerequisites

- [Claude Code](https://claude.ai/code) (CLI or desktop app)
- [Node.js](https://nodejs.org) ≥ 18 (for MCP servers)
- [uv](https://docs.astral.sh/uv/) (Python package manager — used by the eval script)

Install uv if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd pain-point-researcher
npm install
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Open `.env` and fill in each key:

| Key | Where to get it | Required for |
|-----|----------------|--------------|
| `FIRECRAWL_API_KEY` | [firecrawl.dev](https://firecrawl.dev) → API Keys | Scraping X/Twitter, Quora, Reddit URL discovery |
| `EXA_API_KEY` | [exa.ai](https://exa.ai) → Dashboard → API Keys | LinkedIn and Reddit neural search |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys | Eval check 3 (ICE score calibration via LLM judge) |

> `ANTHROPIC_API_KEY` is only needed if you run the eval with LLM judge enabled (i.e. without `--skip-llm`). The main research pipeline runs entirely through Claude Code and does not require it separately.

### 3. Run a research cycle

```bash
claude "Research pain points for [role] in [industry]"
```

Examples:

```bash
claude "Research pain points for independent restaurant owners"
claude "Research pain points for e-commerce operators running Shopify stores"
claude "Research pain points for HR managers at mid-size B2B companies"
claude "Research pain points for wealth managers of high net worth clients"
```

The researcher orchestrator will sequence the scraper, analyst, and competitive-intel subagents automatically and write a dated report to `reports/`.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│               @researcher (orchestrator)                     │
│          sequences subagents, writes final report           │
├───────────────┬──────────────────┬──────────────────────────┤
│   @scraper    │    @analyst      │   @competitive-intel      │
│   Subagent    │    Subagent      │   Subagent                │
│               │                  │                           │
│  Reddit:      │  Deduplicates &  │  Firecrawl MCP searches  │
│  Firecrawl    │  categorizes     │  for solution providers,  │
│  (URL disco.) │  findings, then  │  profiles pricing and     │
│  + reddit_    │  scores with     │  positioning              │
│  fetch.py     │  ICE + WTP       │                           │
│  (content)    │                  │                           │
│               │                  │                           │
│  LinkedIn:    │                  │                           │
│  Exa MCP      │                  │                           │
│  neural search│                  │                           │
│               │                  │                           │
│  X/Twitter    │                  │                           │
│  & Quora:     │                  │                           │
│  Firecrawl    │                  │                           │
│  MCP          │                  │                           │
└───────────────┴──────────────────┴──────────────────────────┘
        │                │                     │
        ▼                ▼                     ▼
   data/raw/      data/analyzed/       data/competitors/
                        │
                        ▼
            reports/YYYY-MM-DD-[topic].md
```

## Running Evals

After each research cycle, run the eval suite to verify report quality before sharing it.

```bash
uv run --with anthropic python scripts/eval_report.py --date YYYY-MM-DD --industry [slug]
```

### Basic usage

```bash
# Full eval with LLM judge (requires ANTHROPIC_API_KEY)
uv run --with anthropic python scripts/eval_report.py --date 2026-05-25 --industry wealth-management

# Skip the LLM judge (faster, no API key needed)
uv run --with anthropic python scripts/eval_report.py --date 2026-05-25 --industry wealth-management --skip-llm

# Amend the report in place with reconciled scores and flagged quotes
uv run --with anthropic python scripts/eval_report.py --date 2026-05-25 --industry wealth-management --amend
```

### Options

| Flag | Description |
|------|-------------|
| `--date` | Date of the research run, e.g. `2026-05-25` (required) |
| `--industry` | Industry slug matching the report filename, e.g. `wealth-management` (required) |
| `--skip-llm` | Skip check 3 (ICE score calibration). Faster; does not require `ANTHROPIC_API_KEY` |
| `--amend` | After running checks, patch the analyzed JSON with reconciled scores and append an "Eval Findings" section to the final report. Requires LLM judge — incompatible with `--skip-llm` |
| `--base` | Project root directory if running from outside the repo (default: `.`) |

### What each check does

**Check 1 — Quote grounding**: Verifies that every `representative_quote` in the analyzed JSON can be traced back to a raw source record via token-overlap matching (≥65%). Flags quotes that may have been paraphrased or hallucinated by the analyst.

**Check 2 — Source URL spot-check**: HTTP HEAD-checks a random 20% sample of `source_urls`. Flags any that return 4xx/5xx. (403s from Quora and LinkedIn are treated as valid — those platforms block bots even on live pages.)

**Check 3 — ICE score calibration** *(requires `ANTHROPIC_API_KEY`)*: Uses `claude-opus-4-7` as an independent judge to re-score each pain point's Impact, Confidence, Ease, and Willingness-to-Pay. Flags any dimension where the stored score and judge score diverge by more than 2 points.

**Check 4 — Platform coverage gate**: Flags platforms with fewer than 10 posts (warning) or fewer than 5 (critical), indicating the scraper may have under-collected.

### Outputs

- **Eval report**: saved to `reports/YYYY-MM-DD-[industry]-eval.md` regardless of pass/fail
- **Exit code 0** if all checks pass; **exit code 1** if any fail (useful in CI)

### With `--amend`

When `--amend` is passed, the script also:

1. **Patches `data/analyzed/YYYY-MM-DD-[industry]-analysis.json`** — overwrites ICE scores and WTP with reconciled values wherever the judge diverged by >2 points, and adds an `amended_at` timestamp
2. **Appends an "Eval Findings" section to `reports/YYYY-MM-DD-[industry]-pain-points.md`** — includes:
   - Unverified quotes that should be manually replaced with verbatim source text
   - A reconciled scores table showing what changed and the delta in total ICE score
   - An adjusted priority rankings table with rank shifts (▲/▼) and `*` markers on amended items

The amendment is additive — the original report content is never overwritten. Running `--amend` multiple times appends a new timestamped section each time.

## Directory Structure

```
pain-point-researcher/
├── .claude/
│   ├── settings.json              # MCP server config + hooks
│   ├── agents/
│   │   ├── researcher.md          # Orchestrator agent
│   │   ├── scraper.md             # Web scraping subagent
│   │   ├── analyst.md             # Synthesis & prioritization subagent
│   │   └── competitive-intel.md   # Competitor mapping subagent
│   └── skills/
│       ├── scrape-community.md
│       ├── prioritize-pain-points.md
│       └── competitor-analysis.md
├── CLAUDE.md                      # Project conventions & data schemas
├── main.py                        # Optional entry point
├── scripts/
│   ├── reddit_fetch.py            # Fetches Reddit posts via public JSON API
│   ├── backup-data.sh             # PreCompact hook: backs up data/
│   └── schedule-run.sh            # Cron wrapper for recurring runs
├── data/
│   ├── raw/                       # Raw scraped records (JSON)
│   ├── analyzed/                  # Scored pain point findings (JSON)
│   └── competitors/               # Competitor profiles (JSON)
├── logs/                          # Run logs
├── reports/                       # Final markdown deliverables
├── templates/
│   └── report-template.md         # Report structure template
├── .env.example                   # API key template
├── pyproject.toml                 # Python dependencies (uv)
└── package.json                   # Node dependencies (Firecrawl/Exa MCP)
```
