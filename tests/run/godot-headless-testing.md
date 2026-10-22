# godot-headless-testing

## SKILL.md `warnings/`

## SKILL.md `level in tree`

<!-- check: prepare -->
```gdscript
var level := Node2D.new()
level.name = "Level"
var packed := PackedScene.new()
packed.pack(level)
ResourceSaver.save(packed, "res://level.tscn")
level.free()
```

## SKILL.md `Input.action_press("jump")`

## SKILL.md `class_has_method("Node"`

## references/smoke-scripts.md `ErrorCounter`

<!-- check: prepare -->
```gdscript
var script_file := FileAccess.open("res://player.gd", FileAccess.WRITE)
script_file.store_string("extends CharacterBody2D\n\nfunc _physics_process(_delta: float) -> void:\n\tif Input.is_action_pressed(&\"right\"):\n\t\tvelocity.x = 200.0\n\telse:\n\t\tvelocity.x = 0.0\n\tmove_and_slide()\n")
script_file.close()
var level := Node2D.new()
level.name = "Level"
var player := CharacterBody2D.new()
player.name = "Player"
player.set_script(load("res://player.gd"))
level.add_child(player)
player.owner = level
var packed := PackedScene.new()
packed.pack(level)
ResourceSaver.save(packed, "res://level.tscn")
level.free()
```

## references/smoke-scripts.md `_collect`

## references/smoke-scripts.md `var hits`

## references/smoke-scripts.md `save_png`

<!-- run: mode render -->

<!-- check: prepare -->
```gdscript
var level := Node2D.new()
level.name = "Level"
var rect := ColorRect.new()
rect.color = Color.RED
rect.size = Vector2(200, 200)
level.add_child(rect)
rect.owner = level
var packed := PackedScene.new()
packed.pack(level)
ResourceSaver.save(packed, "res://level.tscn")
level.free()
```

## references/smoke-scripts.md `class_get_property_list`
