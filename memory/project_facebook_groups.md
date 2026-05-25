---
name: project-facebook-groups
description: Facebook Groups evaluated as a potential data source; user deferred the work
metadata:
  type: project
---

Facebook Groups was considered as a 5th data source alongside Reddit, LinkedIn, X/Twitter, and Quora.

Three options were evaluated:
1. Exa neural search with `includeDomains: ["facebook.com"]` — zero friction but thin data expected
2. Apify Facebook Groups Scraper — most reliable, requires new paid service + `APIFY_API_KEY`
3. Firecrawl `site:facebook.com/groups` search — not viable, FB blocks scrapers

**Why:** User decided to hold off for now. No timeline given.

**How to apply:** Don't suggest Facebook Groups work unless user brings it up. If revisited, Option 2 (Apify) is the recommended path.
