---
type: regex
pattern: 'set_cells_terrain_(connect|path)\([^\n]*-1|(const|var) +\w+ *(:=|: *int *=) *-1\b'
match: contains
target: { source: file, path: player.gd }
---
