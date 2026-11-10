#!/usr/bin/env bash
set -e
. "$(dirname "$0")/../_fixtures/wav.sh"
project main.tscn
buses Music SFX
wav death 900
cat > enemy.gd <<'P'
extends Area2D

signal died

@export var hp := 3


func take_damage(amount: int) -> void:
	hp -= amount
	if hp <= 0:
		die()


func die() -> void:
	died.emit()
	queue_free()
P
cat > enemy.tscn <<'P'
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://enemy.gd" id="1"]

[sub_resource type="CircleShape2D" id="1"]
radius = 16.0

[node name="Enemy" type="Area2D"]
script = ExtResource("1")

[node name="Sprite" type="Sprite2D" parent="."]

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("1")
P
cat > main.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="PackedScene" path="res://enemy.tscn" id="1"]

[node name="Main" type="Node2D"]

[node name="Camera2D" type="Camera2D" parent="."]

[node name="EnemyA" parent="." instance=ExtResource("1")]
position = Vector2(80, 0)

[node name="EnemyB" parent="." instance=ExtResource("1")]
position = Vector2(-80, 0)
P
