---
name: prioritize-pain-points
description: >
  Apply the ICE+WTP prioritization framework to a set of extracted pain points.
  Use after clustering raw data into distinct pain point categories.
---

## Prioritize Pain Points Skill

### Framework: ICE + Willingness-to-Pay

For each pain point, score three dimensions (1-10) then apply a WTP multiplier.

### Scoring Guide

**Impact (1-10)** — Business outcome severity
| Score | Signal in Data |
|-------|---------------|
| 9-10  | "We lost $X", "nearly shut down", "existential risk", revenue/customer loss quantified |
| 7-8   | "Costs us hours every week", "bleeding money", specific cost or time waste cited |
| 5-6   | "Really frustrating", "slows us down", clear efficiency drag |
| 3-4   | "Annoying but manageable", workarounds mentioned |
| 1-2   | "Would be nice", minor quality-of-life issue |

**Confidence (1-10)** — Evidence strength
| Score | Signal in Data |
|-------|---------------|
| 9-10  | 15+ mentions, multiple platforms, specific and consistent details |
| 7-8   | 8-14 mentions, good specificity, at least 2 platforms |
| 5-6   | 4-7 mentions, or many mentions but vague |
| 3-4   | 2-3 mentions, limited detail |
| 1-2   | Single mention, anecdotal, possibly outlier |

**Ease (1-10)** — Consulting fit
| Score | Signal in Data |
|-------|---------------|
| 9-10  | Strategy/process problem, clear scoping, typical consulting engagement |
| 7-8   | Needs some specialization but strong consulting fit |
| 5-6   | Mix of consulting + implementation, could productize |
| 3-4   | Heavily tech-dependent, needs ongoing ops |
| 1-2   | Pure software problem, consulting adds little value |

**WTP Multiplier** — Buying signals
| Multiplier | Signal in Data |
|-----------|---------------|
| 1.5x     | "We spent $X on", "budget for", "hired a consultant for", "paying too much for" |
| 1.2x     | "Anyone recommend", "looking for help with", "best service for" |
| 1.0x     | Pure complaint, no buying intent signals |

### Calculation
```
Final Score = ((Impact + Confidence + Ease) / 3) × WTP Multiplier
```

### Output
Rank all pain points by Final Score descending. For each, include:
- Pain point name and description
- Category (from CLAUDE.md schema)
- All four scores with brief justification
- Final Score
- Representative quotes (2-3, anonymized)
- Source count and platform breakdown
- Business sizes affected
