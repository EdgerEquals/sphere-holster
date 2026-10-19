#!/bin/bash
# Runs inside the pinned simvia/code_aster container.
# 1) our cantilever study (asserted against analytic value by check_aster.py)
# 2) the bundled forma01a verification test if the image ships the test suite
set -o pipefail
cd "$(dirname "$0")"
mkdir -p out
[ -f /home/user/.bashrc ] && source /home/user/.bashrc >/dev/null 2>&1 || true
RA=$(command -v run_aster || ls /opt/*/bin/run_aster /opt/*/*/bin/run_aster 2>/dev/null | head -n1)
echo "run_aster: $RA"
"$RA" --version 2>&1 | tee out/version.txt || true
"$RA" cantilever.export > out/run_cantilever.log 2>&1
echo "CANTILEVER_RC=$?" | tee out/status.txt
tail -n 30 out/run_cantilever.log
TESTDIR=$(dirname "$(find / -name 'forma01a.export' -not -path '*/proc/*' 2>/dev/null | head -n1)" 2>/dev/null)
if [ -n "$TESTDIR" ] && [ -f "$TESTDIR/forma01a.export" ]; then
  echo "bundled tests at $TESTDIR"
  "$RA" --test --wrkdir /tmp/forma01a "$TESTDIR/forma01a.export" > out/run_forma01a.log 2>&1 \
    || "$RA" --test "$TESTDIR/forma01a.export" > out/run_forma01a.log 2>&1
  echo "FORMA01A_RC=$?" | tee -a out/status.txt
  grep -E "DIAGNOSTIC|<OK>|NOOK|OK " out/run_forma01a.log | tail -n 5
else
  echo "FORMA01A_RC=absent" | tee -a out/status.txt
fi
exit 0
