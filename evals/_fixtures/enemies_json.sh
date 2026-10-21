#!/usr/bin/env bash
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "Forward Plus")
P
mkdir -p data
cat > data/enemies.json <<'P'
{
	"slime": {"hp": 20, "speed": 40, "sprite": "res://art/slime.png"},
	"bat": {"hp": 8, "speed": 120, "sprite": "res://art/bat.png"},
	"golem": {"hp": 150, "speed": 25, "sprite": "res://art/golem.png"}
}
P
cat > enemy.gd <<'P'
extends CharacterBody2D

var hp: int
var speed: float

func setup(kind: String) -> void:
	var file := FileAccess.open("res://data/enemies.json", FileAccess.READ)
	var data: Dictionary = JSON.parse_string(file.get_as_text())
	var entry: Dictionary = data[kind]
	hp = entry["hp"]
	speed = entry["speed"]
	var sprite := Sprite2D.new()
	sprite.texture = load(entry["sprite"])
	add_child(sprite)

func _physics_process(_delta: float) -> void:
	velocity = Vector2.LEFT * speed
	move_and_slide()
P
cat > main.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://enemy.gd" id="1"]

[node name="Main" type="Node2D"]

[node name="Enemy" type="CharacterBody2D" parent="."]
script = ExtResource("1")
P
