#!/usr/bin/env bash
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://flock.tscn"
config/features=PackedStringArray("4.7", "Forward Plus")
P
cat > flock.gd <<'P'
extends Node2D

const COUNT := 4000
const WINDOW := 24

var _pos := PackedVector2Array()
var _vel := PackedVector2Array()
var _next: Array[Vector2] = []


func _ready() -> void:
	_pos.resize(COUNT)
	_vel.resize(COUNT)
	_next.resize(COUNT)
	for i in COUNT:
		_pos[i] = Vector2(float(i % 80) * 12.0, float(i / 80) * 12.0)
		_vel[i] = Vector2.RIGHT.rotated(float(i) * 0.1) * 40.0


func _physics_process(delta: float) -> void:
	var id := WorkerThreadPool.add_group_task(_steer, COUNT)
	WorkerThreadPool.wait_for_group_task_completion(id)
	for i in COUNT:
		_vel[i] = _next[i]
		_pos[i] += _vel[i] * delta
	queue_redraw()


func _steer(i: int) -> void:
	var p := _pos[i]
	var push := Vector2.ZERO
	var align := Vector2.ZERO
	for j in range(maxi(0, i - WINDOW), mini(COUNT, i + WINDOW)):
		if j == i:
			continue
		var d := p - _pos[j]
		var dist_sq := d.length_squared()
		if dist_sq < 400.0 and dist_sq > 0.0:
			push += d / dist_sq
		align += _vel[j]
	_next[i] = (_vel[i] + push * 20.0 + align * 0.001).limit_length(80.0)


func _draw() -> void:
	for i in COUNT:
		draw_rect(Rect2(_pos[i], Vector2(2.0, 2.0)), Color.WHITE)
P
cat > flock.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://flock.gd" id="1"]

[node name="Flock" type="Node2D"]
script = ExtResource("1")
P
