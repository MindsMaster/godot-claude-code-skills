---
type: regex
pattern: 'texture\s*\(\s*TEXTURE'
match: not_contains
target: { source: file, path: flash.gdshader }
---
