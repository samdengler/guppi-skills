#!/bin/sh
# Round-trip test for a tracker store: builds a four-task epic with a diamond
# dependency graph and checks that `bd ready` returns the parallel frontier at
# each step. Usage: roundtrip.sh <store-dir>
set -eu
store=${1:?store dir required}
bd="$store/bin/bd"

ids() { "$bd" ready --json 2>/dev/null | jq -r '.[].id' | grep -v '^trk-[a-z0-9]*$' | sort | tr '\n' ' '; }
expect() { got=$(ids); [ "$got" = "$1" ] || { echo "FAIL: ready = '$got', expected '$1'"; exit 1; }; echo "ok: ready = $1"; }

epic=$("$bd" create "Round trip epic" -t epic -p 1 --json | jq -r .id)
a=$("$bd" create "A design note" -p 1 --parent "$epic" --json | jq -r .id)
b=$("$bd" create "B gateway config" -p 1 --parent "$epic" --json | jq -r .id)
c=$("$bd" create "C cedar policy" -p 1 --parent "$epic" --json | jq -r .id)
d=$("$bd" create "D integration test" -p 1 --parent "$epic" --json | jq -r .id)
"$bd" dep add "$b" "$a" -q; "$bd" dep add "$c" "$a" -q
"$bd" dep add "$d" "$b" -q; "$bd" dep add "$d" "$c" -q

expect "$a "
"$bd" close "$a" -r "roundtrip" -q
expect "$b $c "
"$bd" close "$b" -r "roundtrip" -q
expect "$c "
"$bd" close "$c" -r "roundtrip" -q
expect "$d "
"$bd" close "$d" -r "roundtrip" -q
"$bd" close "$epic" -r "roundtrip" -q
echo "PASS: diamond dependency graph resolved in order on $(uname -s)"
