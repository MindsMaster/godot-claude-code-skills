---
type: regex
pattern: 'attenuation_filter|volume_db|unit_size'
match: not_contains
target: { source: file, path: main.tscn }
---
