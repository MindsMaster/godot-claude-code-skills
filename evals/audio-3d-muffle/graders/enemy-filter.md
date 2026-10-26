---
type: regex
pattern: 'attenuation_filter_cutoff_hz = 20500|attenuation_filter_db = 0'
match: not_contains
target: { source: file, path: gun.tscn }
---
