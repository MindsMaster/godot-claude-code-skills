#!/usr/bin/env bash
set -e
. "$(dirname "$0")/../_fixtures/wav.sh"
project main.tscn
cat >> project.godot <<'P'

[autoload]

BulletTime="*res://bullet_time.gd"
P
buses Music SFX
wav music 8000
wav growl 8000
wav wind 8000
cat > bullet_time.gd <<'P'
extends Node

@export var slow_scale := 0.3


func enter() -> void:
	Engine.time_scale = slow_scale


func exit() -> void:
	Engine.time_scale = 1.0
P
cat > enemy.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="AudioStream" path="res://growl.wav" id="1"]

[node name="Enemy" type="Node2D"]

[node name="Growl" type="AudioStreamPlayer2D" parent="."]
stream = ExtResource("1")
autoplay = true
bus = &"SFX"
P
cat > spawner.gd <<'P'
extends Node2D

const ENEMY := preload("res://enemy.tscn")


func spawn(at: Vector2) -> Node2D:
	var enemy := ENEMY.instantiate() as Node2D
	enemy.position = at
	add_child(enemy)
	return enemy
P
cat > main.tscn <<'P'
[gd_scene load_steps=4 format=3]

[ext_resource type="AudioStream" path="res://music.wav" id="1"]
[ext_resource type="AudioStream" path="res://wind.wav" id="2"]
[ext_resource type="Script" path="res://spawner.gd" id="3"]

[node name="Main" type="Node2D"]

[node name="Camera2D" type="Camera2D" parent="."]

[node name="Music" type="AudioStreamPlayer" parent="."]
stream = ExtResource("1")
autoplay = true
bus = &"Music"

[node name="Wind" type="AudioStreamPlayer" parent="."]
stream = ExtResource("2")
autoplay = true
bus = &"SFX"

[node name="Spawner" type="Node2D" parent="."]
script = ExtResource("3")
P
