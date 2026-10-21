#!/usr/bin/env bash
set -e
bash "$(dirname "$0")/../_fixtures/broken_player.sh"
# 评测沙箱只能访问工作目录
mkdir .bin
cp "${GODOT_BIN:-/home/user/ref/bin/godot}" .bin/godot
