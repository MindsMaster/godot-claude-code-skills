#!/usr/bin/env bash
set -e
bash "$(dirname "$0")/../_fixtures/hd2d3d.sh"
old='transform = Transform3D(1, 0, 0, 0, 0.707, 0.707, 0, -0.707, 0.707, 0, 6, 0)'
new='transform = Transform3D(0, -0.707, 0.707, 0, 0.707, 0.707, -1, 0, 0, 0, 6, 0)'
grep -qF "$old" main.tscn
sed -i "s/$old/$new/" main.tscn
grep -qF "$new" main.tscn
