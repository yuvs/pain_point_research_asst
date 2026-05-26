Present a structured intake form using the AskUserQuestion tool with ALL FOUR of the following questions in a single call. Do NOT begin any research or call any other tools until the form has been answered.

**Question 1 — Industry / Vertical**
- Header: "Industry"
- Question: "What is the target industry or vertical?"
- multiSelect: false
- Options:
  - label: "Healthcare / Medical", description: "Independent physician practices, urgent care, clinics"
  - label: "Dental", description: "Dental offices, DSO-adjacent practices"
  - label: "Financial Services", description: "Wealth management, RIAs, accounting firms"
  - label: "Restaurant / Hospitality", description: "Independent restaurants, food & beverage operators"

**Question 2 — Niche / Segment**
- Header: "Niche"
- Question: "What specific niche or segment within that industry?"
- multiSelect: false
- Options:
  - label: "Independent / solo practice", description: "Single-owner, no group affiliation"
  - label: "Small group (2–15 practitioners)", description: "Owner-operated multi-provider"
  - label: "Franchise / multi-location", description: "Owner operates 2+ locations"
  - label: "Mid-market operator", description: "50–250 employees, professional management layer"

**Question 3 — Ideal Company Size**
- Header: "Company size"
- Question: "What is the ideal company size? (select all that apply)"
- multiSelect: true
- Options:
  - label: "Micro (1–10 employees)", description: "Solo operators and very small teams"
  - label: "Small (11–50 employees)", description: "Small business with a management layer"
  - label: "Mid-size (51–250 employees)", description: "Established business, some specialization"
  - label: "Enterprise (250+ employees)", description: "Large organization, complex operations"

**Question 4 — Trade Publication Scope**
- Header: "Publications"
- Question: "What trade publication coverage should we prioritize? (select all that apply)"
- multiSelect: true
- Options:
  - label: "US-focused publications only", description: "Exclude international / non-US editorial"
  - label: "Practitioner-written editorials & op-eds", description: "Bylined by owners or clinicians"
  - label: "Case studies & practice spotlights", description: "Named practices describing real problems"
  - label: "Reader forums & Q&A columns", description: "Letters to the editor, advice columns"

---

After the form is submitted, construct a ResearchBrief:

```json
{
  "industry": "<Q1 answer>",
  "niche": "<Q2 answer>",
  "company_sizes": ["<each Q3 selection>"],
  "publication_scope": {
    "geography": "<'US' if Q4 includes 'US-focused', otherwise 'global'>",
    "content_types": ["<each Q4 selection>"]
  },
  "date": "<today YYYY-MM-DD>",
  "slug": "<kebab-case from industry + niche, 3–5 words>"
}
```

Slug examples: "Dental" + "Independent / solo practice" → `dental-independent` | "Healthcare / Medical" + "Small group" → `medical-small-group`

Display a compact summary to the user:

```
Research Brief
─────────────────────────────
Industry:      [industry]
Niche:         [niche]
Company sizes: [sizes]
Geography:     [geography]
Publications:  [content_types]
Slug:          [slug]
─────────────────────────────
Launching researcher…
```

Then immediately delegate to the `@researcher` subagent, passing the full ResearchBrief. Do not ask for further confirmation.
