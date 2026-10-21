---
type: regex
pattern: 'parse_string|JSON\.parse|JSON\.new'
match: not_contains
target: { source: file, path: enemy.gd }
---
