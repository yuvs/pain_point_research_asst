# Pain Point Research Assistant

## Project Purpose
This is a multi-agent research system for a consulting business. It monitors online communities
(Reddit, LinkedIn, X/Twitter, Quora) to identify business owner pain points, prioritize them,
and map the competitive landscape of firms offering solutions.

## Key Conventions
- All raw scraped data goes to `data/raw/` as timestamped JSON files
- Analysis outputs go to `data/analyzed/` as JSON
- Competitor profiles go to `data/competitors/` as JSON
- Final reports go to `reports/` as markdown files named `YYYY-MM-DD-[topic].md`
- Never overwrite previous reports — each run creates a new dated file
- Always include source URLs and timestamps in scraped data

## Data Schema

### Raw Scrape Record (data/raw/)
```json
{
  "source": "reddit|linkedin|x|quora",
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
  "market_position": "leader|challenger|niche|emerging"
}
```

## Search Query Templates
When scraping, use these query patterns per platform:

- **Reddit**: `site:reddit.com "[industry]" ("struggling with" OR "biggest challenge" OR "pain point" OR "frustrating" OR "wish there was" OR "anyone else deal with")`
- **LinkedIn**: `site:linkedin.com/posts "[industry]" ("challenge" OR "lesson learned" OR "mistake" OR "struggling")`
- **X/Twitter**: `site:x.com "[industry]" ("anyone else" OR "so frustrated" OR "biggest problem" OR "wish there was")`
- **Quora**: `site:quora.com "[industry]" ("biggest challenge" OR "hardest part" OR "how do you handle")`

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
1. `@scraper` collects raw data from all four platforms
2. `@analyst` reads raw data, deduplicates, categorizes, and scores
3. `@competitive-intel` takes the top pain points and finds solution providers
4. `@researcher` (orchestrator) sequences the above and produces the final report

## MCP Servers
- **Firecrawl**: Web scraping and search — `npx -y firecrawl-mcp` (used for X/Twitter and Quora)
- **Exa**: Neural search with content retrieval — `npx -y exa-mcp-server` (used for LinkedIn)

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
