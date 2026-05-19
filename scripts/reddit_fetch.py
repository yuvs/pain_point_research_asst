#!/usr/bin/env python3
"""Fetch Reddit posts via the public unauthenticated JSON API.

No credentials required. Retrieves full post text, selftext, and top
comments, plus native upvote/comment counts.

Usage:
    python scripts/reddit_fetch.py --urls "https://reddit.com/r/SaaS/comments/abc/title/ https://reddit.com/r/entrepreneur/comments/xyz/title/"

URLs can be space- or comma-separated. Outputs a JSON array of Raw Scrape
Records to stdout. Sleeps 1s between requests to respect Reddit rate limits.
"""

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone

_USER_AGENT = "pain-point-researcher:v1.0 (research tool)"

_OWNER_SIGNALS = [
    "my business", "i own", "as a founder", "my company", "i started", "i founded",
    "we founded", "i built", "i'm building", "i am building", "we built", "my startup",
    "our startup", "my product", "my app", "my saas", "i launched", "we launched",
    "i co-founded", "i cofounded", "bootstrapped", "my side project", "i created",
    "i developed", "my service", "i'm the founder", "i am the founder",
]
_OPERATOR_SIGNALS = [
    "i manage", "i run", "our team", "i oversee", "i'm the ceo", "i am the ceo",
    "i'm the cto", "i am the cto", "i'm the coo", "i lead", "i'm leading",
    "head of", "vp of", "director of", "i'm responsible for",
]
_EMPLOYEE_SIGNALS = [
    "my boss", "at my company", "our department", "my employer", "my manager",
    "i work at", "i work for", "my job", "my workplace",
]
_CONSULTANT_SIGNALS = [
    "my clients", "i advise", "in my practice", "my consulting", "my agency",
    "we work with clients", "i help businesses", "i help companies", "i work with clients",
    "my consultancy",
]

_PAIN_PHRASES = [
    "struggling with", "frustrated by", "biggest challenge", "pain point",
    "wish there was", "can't find", "no solution", "biggest problem",
    "hard to", "difficult to", "so annoying", "doesn't work", "broken",
    "anyone else deal with", "how do you handle", "lesson learned",
]


def classify_author(text: str) -> str:
    t = text.lower()
    if any(s in t for s in _OWNER_SIGNALS):
        return "business_owner"
    if any(s in t for s in _OPERATOR_SIGNALS):
        return "operator"
    if any(s in t for s in _EMPLOYEE_SIGNALS):
        return "employee"
    if any(s in t for s in _CONSULTANT_SIGNALS):
        return "consultant"
    return "unknown"


def extract_pain_signals(text: str) -> list[str]:
    signals = []
    for phrase in _PAIN_PHRASES:
        if phrase not in text.lower():
            continue
        for sentence in text.replace("\n", " ").split(". "):
            if phrase in sentence.lower() and len(sentence.strip()) > 20:
                signals.append(sentence.strip()[:200])
                break
    return signals[:5]


def fetch_post(url: str) -> dict | None:
    json_url = url.rstrip("/") + ".json"
    req = urllib.request.Request(json_url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
    except Exception as e:
        print(f"Warning: could not fetch {url}: {e}", file=sys.stderr)
        return None

    try:
        post = data[0]["data"]["children"][0]["data"]

        top_comments = []
        for child in data[1]["data"]["children"][:3]:
            if child.get("kind") == "t1":
                body = child["data"].get("body", "").strip()
                if len(body) > 20:
                    top_comments.append(body[:500])

        title = post.get("title", "")
        selftext = post.get("selftext", "")
        full_text = f"{title}\n\n{selftext}".strip()
        if top_comments:
            full_text += "\n\nTop comments:\n" + "\n---\n".join(top_comments)

        return {
            "source": "reddit",
            "subreddit_or_group": f"r/{post.get('subreddit', '')}",
            "url": f"https://www.reddit.com{post.get('permalink', '')}",
            "author_type": classify_author(full_text),
            "content": full_text[:2000],
            "title": title,
            "engagement": {
                "upvotes": post.get("score", 0),
                "comments": post.get("num_comments", 0),
                "shares": 0,
            },
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "pain_point_signals": extract_pain_signals(full_text),
            "scrape_method": "reddit_json_api",
        }
    except (KeyError, IndexError) as e:
        print(f"Warning: could not parse {url}: {e}", file=sys.stderr)
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Reddit posts via public JSON API")
    parser.add_argument("--urls", required=True, help="Space- or comma-separated Reddit post URLs")
    args = parser.parse_args()

    urls = [u.strip() for u in args.urls.replace(",", " ").split() if u.strip()]
    if not urls:
        print("Error: --urls must be non-empty", file=sys.stderr)
        sys.exit(1)

    records = []
    for i, url in enumerate(urls):
        record = fetch_post(url)
        if record:
            records.append(record)
        if i < len(urls) - 1:
            time.sleep(1)

    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
