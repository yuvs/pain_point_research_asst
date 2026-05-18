#!/bin/bash
# backup-data.sh — Runs before context compaction to preserve data
# Called by the PreCompact hook in .claude/settings.json

BACKUP_DIR="data/backups/$(date +%Y-%m-%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Copy all current data files to backup
for dir in data/raw data/analyzed data/competitors; do
  if [ -d "$dir" ] && [ "$(ls -A "$dir" 2>/dev/null)" ]; then
    cp -r "$dir" "$BACKUP_DIR/"
  fi
done

echo "Backed up data to $BACKUP_DIR"
