#!/usr/bin/env bash
# Deploy harness/server/*.py from this repo to the Vultr harness (/opt/harness).
# Run from the bot's box, only after Danny has OK'd the commit.
#
# For each file: back up the live copy to the next free .revN (never overwrites),
# upload the repo copy in place (keeps owner and mode), py_compile it on the
# server (puts the backup back if that fails), then restart the harness and
# show its status. Never reads or touches /opt/harness/.env, notify.env,
# claude.env or any other secrets.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
HOST="${HARNESS_HOST:-harnessbot@45.76.117.213}"
KEY="${HARNESS_KEY:-$HOME/.ssh/vultr_harnessbot}"
SSH=(ssh -i "$KEY" -o IdentitiesOnly=yes -o BatchMode=yes -o ControlMaster=no "$HOST")
FILES=(server.py repo_tools.py)

# Remote step for one file ($f is set in front). stdin = new file contents.
REMOTE='set -e
cd /opt/harness
n=2; while [ -e "$f.rev$n" ]; do n=$((n+1)); done
[ ! -e "$f.rev$n" ] && cp --preserve=mode,timestamps "$f" "$f.rev$n"
cmp -s "$f" "$f.rev$n"
cat > "$f"
if ! python3 -m py_compile "$f"; then
  cat "$f.rev$n" > "$f"
  echo "py_compile failed for $f; restored from $f.rev$n" >&2
  exit 1
fi
echo "$f: backup $f.rev$n, new copy compiled OK"'

for f in "${FILES[@]}"; do
  python3 -m py_compile "$HERE/$f"
done

for f in "${FILES[@]}"; do
  "${SSH[@]}" "f=$f; $REMOTE" < "$HERE/$f"
done

"${SSH[@]}" 'sudo systemctl restart harness; sleep 3; sudo systemctl status harness --no-pager | head -n 12'
