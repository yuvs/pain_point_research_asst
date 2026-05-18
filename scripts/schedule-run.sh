#!/bin/bash
# schedule-run.sh — Wrapper for cron-based recurring research
#
# Usage:
#   ./scripts/schedule-run.sh "e-commerce" "SMB"
#
# Add to crontab for weekly runs:
#   0 6 * * 1 cd /path/to/pain-point-researcher && ./scripts/schedule-run.sh "e-commerce" "SMB" >> logs/cron.log 2>&1
#
# Or run manually for ad-hoc research on a new vertical:
#   ./scripts/schedule-run.sh "healthcare SaaS" "mid-market"

INDUSTRY="${1:?Usage: schedule-run.sh <industry> [business_size]}"
BIZ_SIZE="${2:-all}"
DATE=$(date +%Y-%m-%d)

echo "=== Research Run: $INDUSTRY ($BIZ_SIZE) — $DATE ==="

# Ensure directories exist
mkdir -p data/raw data/analyzed data/competitors reports logs

# Run the full research pipeline via the orchestrator agent
claude --agent researcher \
  --print \
  --output-format text \
  "Run a complete pain point research cycle for the $INDUSTRY industry. \
   Business size focus: $BIZ_SIZE. \
   Today's date: $DATE. \
   Save all outputs with today's date prefix." \
  2>&1 | tee "logs/$DATE-$INDUSTRY.log"

echo "=== Run complete. Report at reports/$DATE-*.md ==="
