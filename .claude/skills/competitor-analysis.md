---
name: competitor-analysis
description: >
  Research and analyze firms providing solutions to a specific pain point.
  Produces a structured competitive landscape with strengths, weaknesses,
  and market positioning.
---

## Competitor Analysis Skill

### Input
- A specific pain point to research
- Target business size (SMB, mid-market, enterprise)
- Industry context

### Research Procedure

1. **Search for solution providers** using queries:
   - "[pain point] consulting firm"
   - "[pain point] software for [business size]"
   - "[pain point] agency reviews G2 Capterra"
   - "best [pain point] solution [year]"
   - "alternative to [known solution] for [pain point]"

2. **For each provider found**, collect:
   - Website scrape: value proposition, target market, pricing page
   - Review aggregator: G2, Capterra, Clutch, Trustpilot scores
   - Social proof: case studies, notable clients, testimonials

3. **Analyze using SWOT-lite framework**:
   - **Strengths**: What do they do well? (from reviews, case studies)
   - **Weaknesses**: Where do they fall short? (from negative reviews, missing features)
   - **Pricing fit**: Is it accessible to the target business size?
   - **Differentiation**: What's unique about their approach?

4. **Classify market position**:
   - **Leader**: >100 reviews, 4+ star average, well-known brand
   - **Challenger**: Growing review count, 4+ stars, aggressive positioning
   - **Niche**: Few reviews but very high ratings, specialized focus
   - **Emerging**: <20 reviews, new to market, innovative approach

### Output Format
```json
{
  "pain_point": "string",
  "providers": [
    {
      "firm_name": "string",
      "url": "string",
      "type": "consulting|saas|agency|marketplace",
      "target_market": "string",
      "pricing_model": "string",
      "strengths": ["string"],
      "weaknesses": ["string"],
      "differentiation": "string",
      "review_score": "X.X/5 on [platform]",
      "market_position": "leader|challenger|niche|emerging"
    }
  ],
  "white_space": "string — description of gaps in the competitive landscape"
}
```
