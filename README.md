# Pain Point Research Assistant — Claude Code Project

A multi-agent Claude Code system that researches online communities for business pain points, synthesizes findings into prioritized reports, and maps the competitive landscape of solution providers.

## Quick Start

```bash
# 1. Clone this scaffold into your working directory
# 2. Install dependencies
npm install
uv init
uv install firecrawl-py

# 3. Set your API keys
# only if you're using the Anthropic API as opposed to the Pro plan, enter the following:
export ANTHROPIC_API_KEY="sk-ant-..."

# go to firecrawl.dev and sign up for the free plan, and then copy the API from the dashboard page
export FIRECRAWL_API_KEY="fc-..."

# 4. Run the full pipeline
claude --agent researcher "Research pain points for [your target industry] business executives with live Firecrawl MCP access and scrape run"
```

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              Main Orchestrator                    │
│         (You talking to Claude Code)             │
├─────────────┬───────────┬────────────────────────┤
│  @scraper   │ @analyst  │  @competitive-intel     │
│  Subagent   │ Subagent  │  Subagent               │
│             │           │                          │
│  Firecrawl  │ Reads     │  Firecrawl + Search      │
│  MCP for    │ scraped   │  for competitor           │
│  Reddit,    │ data,     │  analysis                 │
│  LinkedIn,  │ applies   │                          │
│  X, Quora   │ framework │                          │
└─────────────┴───────────┴────────────────────────┘
         │              │               │
         ▼              ▼               ▼
    data/raw/      data/analyzed/   data/competitors/
                        │
                        ▼
                reports/YYYY-MM-DD-pain-points.md
```

## Directory Structure

```
pain-point-researcher/
├── .claude/
│   ├── settings.json          # Hooks + MCP server config
│   ├── agents/
│   │   ├── researcher.md      # Top-level orchestrator agent
│   │   ├── scraper.md         # Web scraping subagent
│   │   ├── analyst.md         # Synthesis & prioritization subagent
│   │   └── competitive-intel.md  # Competitor mapping subagent
│   └── skills/
│       ├── scrape-community.md
│       ├── prioritize-pain-points.md
│       └── competitor-analysis.md
├── CLAUDE.md                  # Project memory & conventions
├── scripts/
│   ├── scrape-source.sh       # Hook: validate scrape targets
│   ├── backup-data.sh         # Hook: backup before compaction
│   └── schedule-run.sh        # Cron wrapper for recurring runs
├── data/
│   ├── raw/                   # Raw scraped content (JSON)
│   ├── analyzed/              # Intermediate analysis
│   └── competitors/           # Competitor profiles
├── reports/                   # Final deliverables
├── templates/
│   └── report-template.md     # Report structure template
└── package.json
```
