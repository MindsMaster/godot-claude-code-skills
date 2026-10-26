---
type: regex
pattern: 'add_group_task\([^\n]*\btrue\b'
match: contains
target: { source: file, path: flock.gd }
---
