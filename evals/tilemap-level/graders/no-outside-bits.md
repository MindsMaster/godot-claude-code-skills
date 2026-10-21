---
type: regex
pattern: '(?:\b0:0/0/terrains_peering_bit/(?:top_side|left_side|top_left_corner|top_right_corner|bottom_left_corner)|\b1:0/0/terrains_peering_bit/(?:top_side|top_left_corner|top_right_corner)|\b2:0/0/terrains_peering_bit/(?:top_side|right_side|top_left_corner|top_right_corner|bottom_right_corner)|\b0:1/0/terrains_peering_bit/(?:left_side|top_left_corner|bottom_left_corner)|\b2:1/0/terrains_peering_bit/(?:right_side|top_right_corner|bottom_right_corner)|\b0:2/0/terrains_peering_bit/(?:left_side|bottom_side|top_left_corner|bottom_left_corner|bottom_right_corner)|\b1:2/0/terrains_peering_bit/(?:bottom_side|bottom_left_corner|bottom_right_corner)|\b2:2/0/terrains_peering_bit/(?:right_side|bottom_side|top_right_corner|bottom_left_corner|bottom_right_corner)) = 0'
match: not_contains
target: { source: file, path: main.tscn }
---
