#!/usr/bin/env bash
set -e
bash "$(dirname "$0")/../_fixtures/hd2d3d.sh"
python3 - <<'P'
s = open("main.tscn").read()
old = "transform = Transform3D(1, 0, 0, 0, 0.707, 0.707, 0, -0.707, 0.707, 0, 6, 0)"
new = "transform = Transform3D(0, -0.707, 0.707, 0, 0.707, 0.707, -1, 0, 0, 0, 6, 0)"
assert old in s
open("main.tscn", "w").write(s.replace(old, new))
P
