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

signal health_changed(current: int, maximum: int)
signal score_changed(score: int)

@export var max_health := 100

var health := 100
var score := 0

func take_damage(amount: int) -> void:
	health = maxi(health - amount, 0)
	health_changed.emit(health, max_health)

func add_score(points: int) -> void:
	score += points
	score_changed.emit(score)
P
cat > main.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://player.gd" id="1"]

[node name="Main" type="Node2D"]

[node name="Player" type="CharacterBody2D" parent="."]
script = ExtResource("1")
P
