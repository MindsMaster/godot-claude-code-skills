---
type: regex
pattern: 'hp = max_hp \* 0\.5'
match: not_contains
target: { source: file, path: enemies/slime.gd }
---
