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

## Quick Start

```bash
# 1. Clone and install dependencies
npm install

# 2. Copy the env template and fill in your API keys
cp .env.example .env

# Get your keys:
#   Firecrawl (web scraping):  firecrawl.dev  → API Keys  → paste as FIRECRAWL_API_KEY
#   Exa (neural search):       exa.ai         → Dashboard → paste as EXA_API_KEY
#   Anthropic (optional):      only needed if you're not on the Claude Pro plan

# 3. Run the full pipeline for your target industry
claude "Research pain points for business executives in [your target industry]"

# Examples:
#   claude "Research pain points for independent restaurant owners"
#   claude "Research pain points for e-commerce operators running Shopify stores"
#   claude "Research pain points for HR managers at mid-size B2B companies"
```

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
