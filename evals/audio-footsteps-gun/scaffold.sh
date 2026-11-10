#!/usr/bin/env bash
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "Forward Plus")
P
for name in footstep_1 footstep_2 footstep_3 footstep_4 gun; do
	{
		printf 'RIFF\x24\x58\x01\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\xbb\x00\x00\x00\x77\x01\x00\x02\x00\x10\x00data\x00\x58\x01\x00'
		head -c 88064 /dev/urandom
	} > "$name.wav"
done
cat > default_bus_layout.tres <<'P'
[gd_resource type="AudioBusLayout" format=3]

[resource]
bus/1/name = &"SFX"
bus/1/volume_db = 0.0
bus/1/send = &"Master"
P
cat > player.gd <<'P'
extends Node2D

const FIRE_INTERVAL := 0.08

var _cooldown := 0.0

@onready var _step: AudioStreamPlayer = $Step
@onready var _gun: AudioStreamPlayer = $Gun


# 由走路动画的关键帧调用
func play_step() -> void:
	_step.play()


func _process(delta: float) -> void:
	_cooldown -= delta
	if Input.is_action_pressed("ui_accept") and _cooldown <= 0.0:
		_gun.play()
		_cooldown = FIRE_INTERVAL
P
cat > main.tscn <<'P'
[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://player.gd" id="1"]
[ext_resource type="AudioStream" path="res://footstep_1.wav" id="2"]
[ext_resource type="AudioStream" path="res://gun.wav" id="3"]

[node name="Main" type="Node2D"]

[node name="Player" type="Node2D" parent="."]
script = ExtResource("1")

[node name="Step" type="AudioStreamPlayer" parent="Player"]
stream = ExtResource("2")

[node name="Gun" type="AudioStreamPlayer" parent="Player"]
stream = ExtResource("3")
P
