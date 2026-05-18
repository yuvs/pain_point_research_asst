---
name: scrape-community
description: >
  Scrape a specific online community for pain point signals.
  Use when you need to collect data from a single platform or subreddit
  with specific search parameters.
---

## Scrape Community Skill

When asked to scrape a community for pain points, follow this procedure:

### Input Parameters
- `platform`: reddit | linkedin | x | quora
- `industry`: The target industry or vertical
- `queries`: Array of search queries (or auto-generate from CLAUDE.md templates)
- `max_results`: Maximum posts to collect (default: 20)

### Procedure

1. **Generate search queries** using the templates in CLAUDE.md, substituting
   the target industry. Create 3-4 variations per platform.

2. **Execute searches** using Firecrawl:
   - Use `firecrawl_search` with each query
   - Collect the top results
   - For high-value results, use `firecrawl_scrape` to get full content

3. **Extract structured data** from each result:
   ```json
   {
     "source": "[platform]",
     "url": "[full URL]",
     "title": "[post title]",
     "content": "[full post text, truncated at 2000 chars]",
     "author_type": "[classify based on language signals]",
     "engagement": { "upvotes": 0, "comments": 0 },
     "scraped_at": "[ISO timestamp]",
     "pain_point_signals": ["[extracted phrases indicating frustration/need]"]
   }
   ```

4. **Quality filter**: Skip posts that are:
   - Product promotions or affiliate content
   - Less than 2 meaningful sentences
   - Not from business owners/operators (unless the content is highly relevant)
   - Duplicates of already-collected posts

5. **Save** to `data/raw/YYYY-MM-DD-[industry]-[platform].json`

### Author Classification Signals
- **Business owner**: "my business", "I own", "as a founder", "my company"
- **Operator**: "I manage", "I run", "our team", "I oversee"
- **Employee**: "my boss", "at my company", "we use", "our department"
- **Consultant**: "my clients", "I advise", "in my practice"
- **Unknown**: No clear signals
