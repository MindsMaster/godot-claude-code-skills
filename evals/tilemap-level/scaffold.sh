#!/usr/bin/env bash
set -e
bash "$(dirname "$0")/../_fixtures/platformer2d_tiles.sh"
python3 -I - <<'PY'
import struct
import zlib

size = 48
tile = 16
dirt = (134, 92, 52)
speck = (120, 82, 46)
grass = (88, 168, 64)
edge = (70, 46, 26)
rows = []
for y in range(size):
    row = b"\x00"
    for x in range(size):
        tx = x // tile
        ty = y // tile
        lx = x % tile
        ly = y % tile
        c = dirt
        if (lx + ly) % 7 == 0:
            c = speck
        if ty == 0 and ly < 4:
            c = grass
        if tx == 0 and lx < 2:
            c = edge
        if tx == 2 and lx >= tile - 2:
            c = edge
        if ty == 2 and ly >= tile - 2:
            c = edge
        row += bytes(c) + b"\xff"
    rows.append(row)


def chunk(kind, data):
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(b"".join(rows)))
png += chunk(b"IEND", b"")
open("tiles.png", "wb").write(png)
PY
