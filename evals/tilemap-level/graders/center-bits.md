---
type: regex
pattern: '^(?=[\s\S]*\b1:1/0/terrains_peering_bit/top_side = 0)(?=[\s\S]*\b1:1/0/terrains_peering_bit/right_side = 0)(?=[\s\S]*\b1:1/0/terrains_peering_bit/bottom_side = 0)(?=[\s\S]*\b1:1/0/terrains_peering_bit/left_side = 0)|^(?=[\s\S]*\b1:1/0/terrains_peering_bit/top_left_corner = 0)(?=[\s\S]*\b1:1/0/terrains_peering_bit/top_right_corner = 0)(?=[\s\S]*\b1:1/0/terrains_peering_bit/bottom_right_corner = 0)(?=[\s\S]*\b1:1/0/terrains_peering_bit/bottom_left_corner = 0)'
match: contains
target: { source: file, path: main.tscn }
---
