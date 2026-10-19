#!/bin/bash
# Runs inside the pinned OpenFOAM container. Copies the stock icoFoam
# lid-driven cavity tutorial, meshes it, solves to t = 0.5 s, and leaves the
# logs + final fields in sim/openfoam/out for check_cavity.py.
set -eo pipefail
for rc in /usr/lib/openfoam/openfoam*/etc/bashrc /opt/openfoam*/etc/bashrc; do
  [ -f "$rc" ] && { set +u; source "$rc"; break; }
done
command -v icoFoam >/dev/null || { echo "OpenFOAM environment not found"; exit 1; }
OUT="$(cd "$(dirname "$0")" && pwd)/out"
rm -rf "$OUT/cavity" && mkdir -p "$OUT"
cp -r "$FOAM_TUTORIALS/incompressible/icoFoam/cavity/cavity" "$OUT/cavity"
cd "$OUT/cavity"
echo "OPENFOAM_VERSION=${WM_PROJECT_VERSION}" | tee "$OUT/version.txt"
blockMesh > log.blockMesh 2>&1
icoFoam > log.icoFoam 2>&1
foamListTimes | tail -n 1 > "$OUT/last_time.txt"
tail -n 25 log.icoFoam
