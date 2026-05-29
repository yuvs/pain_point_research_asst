# Pain Point Research Assistant

## Project Purpose
This is a multi-agent research system for a consulting business. It monitors online communities
(Reddit, LinkedIn, X/Twitter, Quora) and industry trade publications to identify business owner
pain points, prioritize them, and map the competitive landscape of firms offering solutions.

## Key Conventions
- All raw scraped data goes to `data/raw/` as timestamped JSON files
- Analysis outputs go to `data/analyzed/` as JSON
- Competitor profiles go to `data/competitors/` as JSON
- Final reports go to `reports/` as markdown files named `YYYY-MM-DD-[topic].md`
- Never overwrite previous reports — each run creates a new dated file
- Always include source URLs and timestamps in scraped data

## ResearchBrief Schema

The `/research-brief` skill collects structured inputs and passes a ResearchBrief to the
researcher agent. Free-form prompts are converted to a minimal brief by the researcher.

```json
{
  "industry": "string — e.g. 'Dental', 'Healthcare / Medical', 'Financial Services'",
  "niche": "string — e.g. 'Independent / solo practice', 'Small group (2–15 practitioners)'",
  "company_sizes": ["Micro (1–10 employees)", "Small (11–50 employees)"],
  "publication_scope": {
    "geography": "US | global",
    "content_types": [
      "Practitioner-written editorials & op-eds",
      "Case studies & practice spotlights",
      "Reader forums & Q&A columns"
    ]
  },
  "date": "YYYY-MM-DD",
  "slug": "kebab-case-slug — used for all output filenames"
}
```

## Data Schema

### Raw Scrape Record (data/raw/)
```json
{
  "source": "reddit|linkedin|x|quora|trade_publication|review_site",
  "subreddit_or_group": "string",
  "url": "string",
  "author_type": "business_owner|operator|employee|consultant|unknown",
  "content": "string",
  "title": "string",
  "engagement": { "upvotes": 0, "comments": 0, "shares": 0 },
  "scraped_at": "ISO-8601",
  "pain_point_signals": ["string"]
}
```

### Analyzed Pain Point (data/analyzed/)
```json
{
  "pain_point": "string",
  "category": "operations|finance|hiring|technology|compliance|marketing|sales|customer_success",
  "frequency": 0,
  "intensity": "critical|high|medium|low",
  "willingness_to_pay": "high|medium|low|unclear",
  "ice_score": { "impact": 0, "confidence": 0, "ease": 0, "total": 0 },
  "representative_quotes": ["string"],
  "source_urls": ["string"],
  "business_sizes": ["smb|mid_market|enterprise"],
  "industries_affected": ["string"]
}
```

### Competitor Profile (data/competitors/)
```json
{
  "firm_name": "string",
  "url": "string",
  "pain_points_addressed": ["string"],
  "pricing_model": "string",
  "target_market": "string",
  "strengths": ["string"],
  "weaknesses": ["string"],
  "differentiation": "string",
  "reviews_sentiment": "positive|mixed|negative",
  "market_position": "leader|challenger|niche|emerging",
  "g2_rating": null,
  "g2_review_count": null,
  "capterra_rating": null,
  "capterra_review_count": null,
  "verified_review_themes": {
    "pros": ["string"],
    "cons": ["string"]
  }
}
```

The `g2_*` / `capterra_*` / `verified_review_themes` fields are optional. Set to `null` when no listing was found. `verified_review_themes.pros` and `.cons` are the top 2–3 recurring themes across G2/Capterra reviews for that provider.

## Search Query Templates
When scraping, use these query patterns per platform. Enrich all queries with
`[niche]` and size-context terms from the ResearchBrief where available.

- **Reddit**: `site:reddit.com "[industry]" "[niche]" ("struggling with" OR "biggest challenge" OR "pain point" OR "frustrating" OR "wish there was" OR "anyone else deal with")`
- **LinkedIn**: `site:linkedin.com/posts "[industry]" "[niche]" ("challenge" OR "lesson learned" OR "mistake" OR "struggling")`
- **X/Twitter**: `site:x.com "[industry]" "[niche]" ("anyone else" OR "so frustrated" OR "biggest problem" OR "wish there was")`
- **Quora**: `site:quora.com "[industry]" "[niche]" ("biggest challenge" OR "hardest part" OR "how do you handle")`
- **Trade Publications**: Exa neural search, NO `includeDomains`. Always `excludeDomains: ["reddit.com", "linkedin.com", "x.com", "twitter.com", "quora.com", "g2.com", "capterra.com"]`. Write queries as article topics, not social complaints. Use `type: "neural"` and `contents: {text: true, maxCharacters: 3000}`. Example: `"[niche] [industry] owner challenges [size_context] 2024 OR 2025 [geography]"`
- **Review Sites (G2 / Capterra)**: Exa neural search with `includeDomains: ["g2.com", "capterra.com"]`. Queries describe the pain: `"[industry] [niche] software cons limitations missing [size_context]"`. Focus on "Cons" sections of reviews. Reviewer's stated job title → `author_type`. `subreddit_or_group` = product category name (e.g., `"Dental Practice Management Software"`). `source: "review_site"`, `scrape_method: "exa_neural_search"`. Save to `data/raw/YYYY-MM-DD-[slug]-review-sites.json`.

## Prioritization Framework: ICE + WTP
We use a modified ICE framework with Willingness-to-Pay overlay:

| Dimension     | Score 1-10 | Criteria |
|---------------|-----------|----------|
| **Impact**    | How severely does this affect business outcomes? |
| **Confidence**| How much evidence do we have? (volume of mentions, specificity) |
| **Ease**      | How feasible is it to build a consulting offering around this? |
| **WTP Multiplier** | 1.0x (unclear), 1.2x (medium), 1.5x (high) — people explicitly mention budget/spend |

**Final Score** = (Impact + Confidence + Ease) / 3 × WTP Multiplier

## Agent Workflow
1. `/research-brief` skill (optional) — collects structured ResearchBrief via intake form
2. `@researcher` (orchestrator) — accepts a ResearchBrief or free-form prompt, sequences subagents
3. `@scraper` — collects raw data from Reddit, LinkedIn, X/Twitter, Quora, Trade Publications, and Review Sites (G2/Capterra)
4. `@analyst` — deduplicates, categorizes, and ICE+WTP scores the findings
5. `@competitive-intel` — profiles solution providers for the top pain points

## MCP Servers
- **Firecrawl**: Web scraping and search — `npx -y firecrawl-mcp` (used for X/Twitter and Quora)
- **Exa**: Neural search with content retrieval — `npx -y exa-mcp-server` (used for LinkedIn and Trade Publications)

Reddit's API is no longer self-serve. Reddit is scraped via Firecrawl search for URL
discovery and `scripts/reddit_fetch.py` for full content (Reddit's public JSON API,
no credentials required).

## Reddit Fetcher Script
`scripts/reddit_fetch.py` — discovers post URLs via Firecrawl search, then fetches
full post text and top comments via Reddit's public `.json` endpoint. Returns Raw
Scrape Records with real upvote/comment counts. No API key needed. Uses Python stdlib
only — no extra dependencies beyond what's already installed.

## Credentials

All credentials live in `.env` (gitignored). Copy `.env.example` → `.env` and fill
in each value. MCP servers source this file automatically on startup.

| Service | Env Var | How to obtain |
|---------|---------|---------------|
| Firecrawl | `FIRECRAWL_API_KEY` | firecrawl.dev → API Keys |
| Exa | `EXA_API_KEY` | exa.ai → Dashboard → API Keys |
| Anthropic | `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys (required for eval check 3) |

## Eval Script

`scripts/eval_report.py` — runs after each research cycle to verify report quality.

```
python scripts/eval_report.py --date 2026-05-25 --industry wealth-management
python scripts/eval_report.py --date 2026-05-25 --industry wealth-management --skip-llm
```

Four checks:
1. **Quote grounding** — verifies `representative_quotes` are traceable to raw source records via exact substring or token-overlap matching (≥65%)
2. **Source URL spot-check** — HTTP HEAD-checks a 20% random sample of `source_urls`; flags 4xx/5xx
3. **ICE score calibration** — uses `claude-opus-4-7` as an independent judge; flags any dimension where stored vs. judge score diverges by >2 points. Requires `ANTHROPIC_API_KEY`. Skip with `--skip-llm`.
4. **Platform coverage gate** — flags platforms with <10 posts (warn) or <5 (critical)

Saves eval report to `reports/YYYY-MM-DD-[industry]-eval.md`. Exits 0 if all checks pass, 1 otherwise.

With `--amend`: patches `data/analyzed/` with reconciled scores, appends an Eval Findings section to `reports/YYYY-MM-DD-[industry]-pain-points.md`, and writes a clean final version to `reports/YYYY-MM-DD-[industry]-pain-points-final.md` (full narrative + Reconciled Priority Rankings table, no eval appendix).
