---
type: regex
pattern: '^(?=[\s\S]*\b0:0/0/terrain_set = 0)(?=[\s\S]*\b1:0/0/terrain_set = 0)(?=[\s\S]*\b2:0/0/terrain_set = 0)(?=[\s\S]*\b0:1/0/terrain_set = 0)(?=[\s\S]*\b1:1/0/terrain_set = 0)(?=[\s\S]*\b2:1/0/terrain_set = 0)(?=[\s\S]*\b0:2/0/terrain_set = 0)(?=[\s\S]*\b1:2/0/terrain_set = 0)(?=[\s\S]*\b2:2/0/terrain_set = 0)'
match: contains
target: { source: file, path: main.tscn }
---
