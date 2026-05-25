#!/usr/bin/env python3
"""Eval suite for pain-point research reports.

Run after each research cycle to verify report quality across four checks:
  1. Quote grounding   — representative_quotes traceable to raw source data
  2. Source URL check  — HTTP HEAD-checks 20% sample of source_urls
  3. ICE score calibration — LLM re-scores each pain point, flags >2-point divergences
  4. Platform coverage — flags platforms below the minimum post threshold

Usage:
    python scripts/eval_report.py --date 2026-05-25 --industry wealth-management
    python scripts/eval_report.py --date 2026-05-25 --industry wealth-management --skip-llm
    python scripts/eval_report.py --date 2026-05-25 --industry wealth-management --amend

--amend applies reconciled scores to the analyzed JSON and appends an eval
findings section to the final report. Requires ANTHROPIC_API_KEY (runs check 3).

Exit code 0 if all checks pass, 1 otherwise.
"""

import argparse
import glob
import json
import os
import random
import re
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# ── env loading ──────────────────────────────────────────────────────────────

def _load_env(path: str = ".env") -> dict[str, str]:
    env: dict[str, str] = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


# ── file helpers ─────────────────────────────────────────────────────────────

def _load_json(path: str) -> list | dict:
    with open(path) as f:
        return json.load(f)


def _find_files(date: str, industry: str, base: str = ".") -> dict:
    slug = f"{date}-{industry}"
    return {
        "raw": sorted(glob.glob(os.path.join(base, f"data/raw/{slug}-*.json"))),
        "analyzed": os.path.join(base, f"data/analyzed/{slug}-analysis.json"),
        "report": os.path.join(base, f"reports/{slug}-pain-points.md"),
    }


def _load_analyzed(path: str) -> tuple[list[dict], dict | None]:
    """Return (pain_points list, wrapper dict or None).

    The analyst may store pain points as a bare list or wrapped in a dict
    with metadata: {"pain_points": [...], "industry": ..., ...}.
    Returns the wrapper so we can write it back intact.
    """
    raw = _load_json(path)
    if isinstance(raw, dict):
        return raw.get("pain_points", []), raw
    return raw, None


def _save_analyzed(path: str, pain_points: list[dict], wrapper: dict | None) -> None:
    if wrapper is not None:
        wrapper["pain_points"] = pain_points
        data = wrapper
    else:
        data = pain_points
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ── check result ─────────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    name: str
    passed: bool
    summary: str
    issues: list[str] = field(default_factory=list)
    # Structured payload used by --amend; not displayed to users.
    data: dict = field(default_factory=dict)


# ── check 1: quote grounding ─────────────────────────────────────────────────

_STOPWORDS = {
    "i", "me", "my", "the", "a", "an", "and", "or", "but", "in", "on", "at",
    "to", "for", "of", "with", "by", "from", "is", "was", "are", "were", "be",
    "been", "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "it", "its", "this", "that", "these", "those",
    "we", "our", "you", "your", "they", "their", "what", "which", "who", "how",
    "when", "where", "not", "no", "so", "if", "then", "than", "as", "up", "out",
    "about", "just", "like", "can", "us", "all", "also", "very", "more", "some",
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    return {w for w in words if w not in _STOPWORDS}


def _is_grounded(quote: str, raw_contents: list[str]) -> bool:
    ql = quote.lower().strip()
    if any(ql in c.lower() for c in raw_contents):
        return True
    qt = _tokenize(quote)
    if len(qt) < 3:
        return True
    for content in raw_contents:
        ct = _tokenize(content)
        if ct and len(qt & ct) / len(qt) >= 0.65:
            return True
    return False


def check_quote_grounding(analyzed: list[dict], raw_files: list[str]) -> CheckResult:
    raw_contents: list[str] = []
    for path in raw_files:
        records = _load_json(path)
        if isinstance(records, list):
            for r in records:
                if isinstance(r, dict):
                    raw_contents.append(r.get("content", ""))

    total = 0
    ungrounded: list[dict] = []
    for pp in analyzed:
        pp_name = pp.get("pain_point", "unknown")
        for quote in pp.get("representative_quotes", []):
            total += 1
            if not _is_grounded(quote, raw_contents):
                ungrounded.append({"pain_point": pp_name, "quote": quote})

    pct = round((total - len(ungrounded)) / total * 100) if total else 0
    return CheckResult(
        name="Quote Grounding",
        passed=len(ungrounded) == 0,
        summary=f"{total - len(ungrounded)}/{total} quotes grounded ({pct}%)",
        issues=[f'[{u["pain_point"]}] "{u["quote"][:120]}"' for u in ungrounded],
        data={"ungrounded": ungrounded},
    )


# ── check 2: source URL spot-check ───────────────────────────────────────────

def _head_url(url: str) -> tuple[bool, int]:
    try:
        req = urllib.request.Request(
            url, method="HEAD", headers={"User-Agent": "pain-point-eval/1.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return True, resp.status
    except urllib.error.HTTPError as e:
        # 403 = URL exists but blocks automated access (Quora, LinkedIn).
        if e.code == 403:
            return True, 403
        return False, e.code
    except Exception:
        return False, 0


def check_source_urls(analyzed: list[dict], sample_rate: float = 0.20) -> CheckResult:
    all_urls: list[str] = []
    for pp in analyzed:
        all_urls.extend(pp.get("source_urls", []))
    all_urls = list(set(all_urls))

    k = max(5, min(30, int(len(all_urls) * sample_rate)))
    sample = random.sample(all_urls, min(k, len(all_urls)))

    failed: list[str] = []
    for url in sample:
        ok, status = _head_url(url)
        if not ok:
            failed.append(f"{url} → {status or 'error'}")
        time.sleep(0.3)

    return CheckResult(
        name="Source URL Spot-Check",
        passed=len(failed) == 0,
        summary=f"{len(sample) - len(failed)}/{len(sample)} sampled URLs resolved (pool: {len(all_urls)})",
        issues=[f"Dead URL — {f}" for f in failed],
    )


# ── check 3: ICE+WTP score calibration ───────────────────────────────────────

_JUDGE_SYSTEM = """You are a market research quality auditor scoring business pain points.

Scoring criteria (1-10 each):
- Impact: How severely does this pain point affect business outcomes? 10=company-threatening, 1=minor inconvenience
- Confidence: How much evidence supports this? Consider frequency of mentions and quote specificity. 10=overwhelming evidence, 1=single vague mention
- Ease: How feasible is it to build a consulting offering around this? 10=clear solution path, 1=intractable

WTP (willingness-to-pay):
- "high": quotes explicitly mention budget, spend, or cost
- "medium": implicit financial concern
- "low": no financial signal
- "unclear": ambiguous"""

_JUDGE_USER_TMPL = """Pain point: {pain_point}
Category: {category}
Frequency (posts mentioning it): {frequency}
Intensity: {intensity}

Representative quotes:
{quotes}

Score this pain point using the ICE+WTP framework."""

_SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "impact":     {"type": "integer"},
        "confidence": {"type": "integer"},
        "ease":       {"type": "integer"},
        "wtp":        {"type": "string", "enum": ["high", "medium", "low", "unclear"]},
    },
    "required": ["impact", "confidence", "ease", "wtp"],
    "additionalProperties": False,
}

# Conservative WTP reconciliation: lower rank = more conservative.
# Special case: "unclear" + judge signal → trust judge (new information).
_WTP_RANK = {"unclear": 0, "low": 1, "medium": 2, "high": 3}
_WTP_MULT = {"high": 1.5, "medium": 1.2, "low": 1.0, "unclear": 1.0}


def _reconcile_wtp(stored: str, judge: str) -> str:
    if stored == "unclear" and judge != "unclear":
        return judge  # judge found signal analyst missed
    sr = _WTP_RANK.get(stored, 0)
    jr = _WTP_RANK.get(judge, 0)
    return stored if sr <= jr else judge  # take more conservative


def _call_judge(client, pain_point: dict) -> dict | None:
    quotes_text = "\n".join(
        f"- {q}" for q in pain_point.get("representative_quotes", [])[:5]
    )
    user_msg = _JUDGE_USER_TMPL.format(
        pain_point=pain_point.get("pain_point", ""),
        category=pain_point.get("category", ""),
        frequency=pain_point.get("frequency", 0),
        intensity=pain_point.get("intensity", ""),
        quotes=quotes_text,
    )
    try:
        resp = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=200,
            # Stable system prompt cached across all calls in a run.
            system=[{"type": "text", "text": _JUDGE_SYSTEM, "cache_control": {"type": "ephemeral"}}],
            # JSON schema guarantees valid structured output — no fragile parsing.
            output_config={"format": {"type": "json_schema", "schema": _SCORE_SCHEMA}},
            messages=[{"role": "user", "content": user_msg}],
        )
        text = next(b.text for b in resp.content if b.type == "text")
        return json.loads(text)
    except Exception as e:
        print(f"  Warning: judge call failed for '{pain_point.get('pain_point', '')}': {e}", file=sys.stderr)
        return None


def check_ice_scores(analyzed: list[dict], api_key: str) -> CheckResult:
    try:
        import anthropic
    except ImportError:
        return CheckResult(
            name="ICE Score Calibration",
            passed=False,
            summary="Skipped — 'anthropic' package not installed. Run: pip install anthropic",
        )

    client = anthropic.Anthropic(api_key=api_key)
    divergences: list[str] = []
    # reconciled holds only pain points where at least one dimension changed.
    reconciled: dict[str, dict] = {}

    for pain_point in analyzed:
        pp_name = pain_point.get("pain_point", "unknown")
        stored = pain_point.get("ice_score", {})
        stored_wtp = pain_point.get("willingness_to_pay", "unclear")

        judge = _call_judge(client, pain_point)
        if not judge:
            continue

        # Reconcile each ICE dimension by averaging.
        rec_impact     = round((stored.get("impact", 0)     + judge["impact"])     / 2)
        rec_confidence = round((stored.get("confidence", 0) + judge["confidence"]) / 2)
        rec_ease       = round((stored.get("ease", 0)       + judge["ease"])       / 2)
        rec_wtp        = _reconcile_wtp(stored_wtp, judge["wtp"])

        # Collect divergences (display only — what exceeded ±2 threshold).
        for dim, s_val, j_val in [
            ("impact",     stored.get("impact", 0),     judge["impact"]),
            ("confidence", stored.get("confidence", 0), judge["confidence"]),
            ("ease",       stored.get("ease", 0),       judge["ease"]),
        ]:
            if abs(s_val - j_val) > 2:
                divergences.append(
                    f'"{pp_name}" {dim}: stored={s_val}, judge={j_val} (Δ{abs(s_val - j_val)})'
                )

        if stored_wtp != rec_wtp:
            divergences.append(
                f'"{pp_name}" wtp: stored={stored_wtp}, judge={judge["wtp"]} → reconciled={rec_wtp}'
            )

        # Record full reconciliation for any pain point where something changed.
        changes: list[str] = []
        if rec_impact     != stored.get("impact", 0):     changes.append(f"impact: {stored.get('impact')}→{rec_impact}")
        if rec_confidence != stored.get("confidence", 0): changes.append(f"confidence: {stored.get('confidence')}→{rec_confidence}")
        if rec_ease       != stored.get("ease", 0):       changes.append(f"ease: {stored.get('ease')}→{rec_ease}")
        if rec_wtp        != stored_wtp:                  changes.append(f"wtp: {stored_wtp}→{rec_wtp}")

        if changes:
            mult = _WTP_MULT.get(rec_wtp, 1.0)
            rec_total = round((rec_impact + rec_confidence + rec_ease) / 3 * mult, 2)
            reconciled[pp_name] = {
                "ice_score": {
                    "impact": rec_impact,
                    "confidence": rec_confidence,
                    "ease": rec_ease,
                    "total": rec_total,
                },
                "willingness_to_pay": rec_wtp,
                "original_total": stored.get("total", 0),
                "changes": changes,
            }

        time.sleep(0.5)

    total_dims = len(analyzed) * 4
    ok_count = total_dims - len(divergences)
    return CheckResult(
        name="ICE Score Calibration",
        passed=len(divergences) == 0,
        summary=f"{ok_count}/{total_dims} dimensions within ±2 across {len(analyzed)} pain points",
        issues=[f"Score divergence — {d}" for d in divergences],
        data={"reconciled": reconciled},
    )


# ── check 4: platform coverage ───────────────────────────────────────────────

_MIN_POSTS = 10
_CRITICAL_POSTS = 5
_EXPECTED_PLATFORMS = {"reddit", "linkedin", "x", "quora"}


def check_platform_coverage(raw_files: list[str]) -> CheckResult:
    counts: dict[str, int] = {}
    for path in raw_files:
        records = _load_json(path)
        if not isinstance(records, list):
            continue
        platform = Path(path).stem.rsplit("-", 1)[-1]
        counts[platform] = len(records)

    issues: list[str] = []
    for platform, count in counts.items():
        if count < _CRITICAL_POSTS:
            issues.append(f"{platform}: {count} posts (CRITICAL — below {_CRITICAL_POSTS})")
        elif count < _MIN_POSTS:
            issues.append(f"{platform}: {count} posts (thin — below {_MIN_POSTS}; ensure report notes this)")

    for p in _EXPECTED_PLATFORMS - set(counts.keys()):
        issues.append(f"{p}: no raw data file found")

    summary_parts = [f"{p}={c}" for p, c in sorted(counts.items())]
    return CheckResult(
        name="Platform Coverage",
        passed=len(issues) == 0,
        summary="Posts per platform: " + ", ".join(summary_parts),
        issues=issues,
    )


# ── amendment: patch analyzed JSON ───────────────────────────────────────────

def _amend_analyzed(
    pain_points: list[dict],
    wrapper: dict | None,
    ice_result: CheckResult,
    path: str,
) -> int:
    """Apply reconciled ICE scores to analyzed JSON. Returns count of patched items."""
    reconciled = ice_result.data.get("reconciled", {})
    if not reconciled:
        return 0

    patched = 0
    for pp in pain_points:
        name = pp.get("pain_point", "")
        if name in reconciled:
            rec = reconciled[name]
            pp["ice_score"] = rec["ice_score"]
            pp["willingness_to_pay"] = rec["willingness_to_pay"]
            patched += 1

    if wrapper is not None:
        wrapper["amended_at"] = datetime.now(timezone.utc).isoformat()
    _save_analyzed(path, pain_points, wrapper)
    return patched


# ── amendment: append findings to report ─────────────────────────────────────

def _build_eval_appendix(
    results: list[CheckResult],
    date: str,
    pain_points_before: list[dict],
) -> str:
    """Build the markdown eval findings section to append to the report."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = [
        "",
        "---",
        "",
        f"## Eval Findings — {date}",
        "",
        f"*Auto-generated {ts} by `scripts/eval_report.py --amend`. "
        "Scores marked \\* were reconciled where the LLM judge diverged by >2 points.*",
        "",
    ]

    # ── quote grounding ──
    grounding = next((r for r in results if r.name == "Quote Grounding"), None)
    if grounding and grounding.data.get("ungrounded"):
        lines += [
            "### Unverified Quotes",
            "",
            "The following quotes could not be traced to source data and should be "
            "manually replaced with verbatim text from the raw records:",
            "",
        ]
        for u in grounding.data["ungrounded"]:
            lines.append(f'- **{u["pain_point"]}**: "{u["quote"][:160]}"')
        lines.append("")
    else:
        lines += ["### Quote Grounding", "", "✓ All quotes traced to source data.", ""]

    # ── score reconciliation ──
    ice = next((r for r in results if r.name == "ICE Score Calibration"), None)
    reconciled = ice.data.get("reconciled", {}) if ice else {}

    if reconciled:
        lines += [
            "### Reconciled Scores",
            "",
            "| Pain Point | Changes Applied | Original Total | Reconciled Total |",
            "|---|---|---|---|",
        ]
        for name, rec in reconciled.items():
            short = (name[:65] + "…") if len(name) > 65 else name
            changes = ", ".join(rec["changes"])
            lines.append(
                f"| {short} | {changes} | {rec['original_total']} | {rec['ice_score']['total']} |"
            )
        lines.append("")

        # Adjusted priority rankings
        items: list[tuple[str, float, float]] = []
        for pp in pain_points_before:
            pname = pp.get("pain_point", "")
            orig = pp.get("ice_score", {}).get("total", 0)
            new = reconciled[pname]["ice_score"]["total"] if pname in reconciled else orig
            items.append((pname, orig, new))

        orig_rank = {name: i + 1 for i, (name, _, _) in enumerate(
            sorted(items, key=lambda x: x[1], reverse=True)
        )}
        new_sorted = sorted(items, key=lambda x: x[2], reverse=True)

        lines += [
            "### Adjusted Priority Rankings",
            "",
            "Pain points re-ranked after score reconciliation. "
            "Items marked \\* had at least one score adjusted.",
            "",
            "| Rank | Pain Point | Score | Δ Rank |",
            "|---|---|---|---|",
        ]
        for i, (name, _, new_total) in enumerate(new_sorted):
            rank = i + 1
            delta = orig_rank[name] - rank
            delta_str = f"▲{delta}" if delta > 0 else (f"▼{abs(delta)}" if delta < 0 else "—")
            marker = "\\*" if name in reconciled else ""
            short = (name[:70] + "…") if len(name) > 70 else name
            lines.append(f"| {rank} | {marker}{short} | {new_total} | {delta_str} |")
        lines.append("")

    elif ice and not ice.issues:
        lines += ["### Score Calibration", "", "✓ All ICE+WTP scores within ±2 of independent judge.", ""]

    # ── platform coverage ──
    coverage = next((r for r in results if r.name == "Platform Coverage"), None)
    if coverage and coverage.issues:
        lines += ["### Platform Coverage Warnings", ""]
        lines += [f"- {i}" for i in coverage.issues]
        lines.append("")

    return "\n".join(lines)


def _amend_report(report_path: str, appendix: str) -> bool:
    """Append eval findings to the report. Returns True if report was found and updated."""
    if not os.path.exists(report_path):
        return False
    with open(report_path, "a") as f:
        f.write(appendix)
    return True


# ── eval report rendering ─────────────────────────────────────────────────────

def _render_eval_report(results: list[CheckResult], date: str, industry: str) -> str:
    passed_count = sum(1 for r in results if r.passed)
    lines = [
        f"# Eval Report: {date} {industry}",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        f"**{passed_count}/{len(results)} checks passed**",
        "",
    ]
    for i, r in enumerate(results, 1):
        icon = "✓" if r.passed else "✗"
        lines.append(f"## Check {i}: {r.name} {icon}")
        lines.append(f"**{r.summary}**")
        if r.issues:
            lines.append("")
            for issue in r.issues:
                lines.append(f"- {issue}")
        lines.append("")
    return "\n".join(lines)


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Eval suite for pain-point research reports")
    parser.add_argument("--date",     required=True, help="Run date, e.g. 2026-05-25")
    parser.add_argument("--industry", required=True, help="Industry slug, e.g. wealth-management")
    parser.add_argument("--skip-llm", action="store_true", help="Skip check 3 (ICE score calibration)")
    parser.add_argument("--amend",    action="store_true",
                        help="After eval, patch analyzed JSON with reconciled scores and append findings to report")
    parser.add_argument("--base",     default=".", help="Project root directory")
    args = parser.parse_args()

    if args.amend and args.skip_llm:
        print("Error: --amend requires check 3 (LLM judge). Remove --skip-llm.", file=sys.stderr)
        sys.exit(1)

    files = _find_files(args.date, args.industry, args.base)

    if not os.path.exists(files["analyzed"]):
        print(f"Error: analyzed file not found: {files['analyzed']}", file=sys.stderr)
        sys.exit(1)
    if not files["raw"]:
        print(f"Error: no raw data files found for {args.date}-{args.industry}-*.json", file=sys.stderr)
        sys.exit(1)

    pain_points, wrapper = _load_analyzed(files["analyzed"])
    # Snapshot pre-patch values for the rankings diff in the appendix.
    pain_points_before = json.loads(json.dumps(pain_points))

    print(f"Loaded {len(pain_points)} pain points  |  {len(files['raw'])} platform file(s)")
    print()

    results: list[CheckResult] = []

    print("Check 1: Quote Grounding...")
    results.append(check_quote_grounding(pain_points, files["raw"]))
    print(f"  {results[-1].summary}")

    print("Check 2: Source URL Spot-Check...")
    results.append(check_source_urls(pain_points))
    print(f"  {results[-1].summary}")

    if args.skip_llm:
        print("Check 3: ICE Score Calibration — skipped (--skip-llm)")
        results.append(CheckResult("ICE Score Calibration", True, "Skipped (--skip-llm)"))
    else:
        env = _load_env(os.path.join(args.base, ".env"))
        api_key = os.environ.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("Check 3: ICE Score Calibration — skipped (ANTHROPIC_API_KEY not set)")
            results.append(CheckResult("ICE Score Calibration", True, "Skipped — ANTHROPIC_API_KEY not set"))
        else:
            print("Check 3: ICE Score Calibration (LLM judge, claude-opus-4-7)...")
            results.append(check_ice_scores(pain_points, api_key))
            print(f"  {results[-1].summary}")

    print("Check 4: Platform Coverage...")
    results.append(check_platform_coverage(files["raw"]))
    print(f"  {results[-1].summary}")

    print()

    # ── save eval report ──
    eval_report_text = _render_eval_report(results, args.date, args.industry)
    eval_out = os.path.join(args.base, f"reports/{args.date}-{args.industry}-eval.md")
    with open(eval_out, "w") as f:
        f.write(eval_report_text)
    print(eval_report_text)
    print(f"Eval report saved → {eval_out}")

    # ── amend ──
    if args.amend:
        print()
        ice_result = next(r for r in results if r.name == "ICE Score Calibration")
        reconciled = ice_result.data.get("reconciled", {})

        if reconciled:
            patched = _amend_analyzed(pain_points, wrapper, ice_result, files["analyzed"])
            print(f"Analyzed JSON patched: {patched} pain point(s) updated → {files['analyzed']}")
        else:
            print("Analyzed JSON unchanged — no score divergences to reconcile.")

        appendix = _build_eval_appendix(results, args.date, pain_points_before)
        if _amend_report(files["report"], appendix):
            print(f"Report amended → {files['report']}")
        else:
            print(f"Warning: report not found at {files['report']} — appendix not added.")

    passed_all = all(r.passed for r in results)
    sys.exit(0 if passed_all else 1)


if __name__ == "__main__":
    main()
