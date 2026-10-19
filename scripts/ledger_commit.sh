#!/usr/bin/env bash
# Commit ledger/ changes to main with append-only verification and rebase-retry (used by the ledger workflows).
# Usage: scripts/ledger_commit.sh "<commit message>" <regenerate command...>
# The regenerate command is re-run after every rebase so concurrent appends never conflict.
set -euo pipefail
msg="$1"; shift
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
for attempt in 1 2 3 4; do
  git fetch -q origin main
  git reset -q --hard origin/main
  git show origin/main:ledger/findings.jsonl > /tmp/ledger_old.jsonl 2>/dev/null || : > /tmp/ledger_old.jsonl
  "$@"
  python scripts/ledger.py verify-append-only --old /tmp/ledger_old.jsonl --new ledger/findings.jsonl
  python scripts/ledger.py validate > /dev/null
  git add ledger/
  if git diff --cached --quiet; then echo "ledger: nothing new"; exit 0; fi
  git commit -qm "$msg"
  if git push -q origin HEAD:main; then echo "ledger: pushed $(git rev-parse --short HEAD)"; exit 0; fi
  echo "push rejected (attempt $attempt), retrying"; sleep $((attempt * 5))
done
echo "::error::could not push ledger update"; exit 1
