#!/usr/bin/env bash
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "Forward Plus")
P
cat > player.gd <<'P'
extends CharacterBody2D

@export var speed := 220.0
@export var jump_velocity := -420.0

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity += get_gravity() * delta
	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		velocity.y = jump_velocity
	velocity.x = Input.get_axis("ui_left", "ui_right") * speed
	move_and_slide()
P
cat > main.tscn <<'P'
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://player.gd" id="1"]

[sub_resource type="RectangleShape2D" id="1"]
size = Vector2(24, 40)

[node name="Main" type="Node2D"]

[node name="Player" type="CharacterBody2D" parent="."]
script = ExtResource("1")

[node name="CollisionShape2D" type="CollisionShape2D" parent="Player"]
shape = SubResource("1")
P
