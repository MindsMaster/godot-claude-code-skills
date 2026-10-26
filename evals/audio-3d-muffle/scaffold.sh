#!/usr/bin/env bash
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "Forward Plus")
P
{
	printf 'RIFF\x24\x58\x01\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\xbb\x00\x00\x00\x77\x01\x00\x02\x00\x10\x00data\x00\x58\x01\x00'
	head -c 88064 /dev/urandom
} > gun.wav
cat > gun.wav.import <<'P'
[remap]

importer="wav"
type="AudioStreamWAV"

[deps]

source_file="res://gun.wav"

[params]

force/8_bit=false
force/mono=false
force/max_rate=false
force/max_rate_hz=44100
edit/trim=false
edit/normalize=false
edit/loop_mode=0
edit/loop_begin=0
edit/loop_end=-1
compress/mode=2
P
cat > gun.gd <<'P'
extends AudioStreamPlayer3D


func fire() -> void:
	play()
P
cat > gun.tscn <<'P'
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://gun.gd" id="1"]
[ext_resource type="AudioStream" path="res://gun.wav" id="2"]

[node name="Gun" type="AudioStreamPlayer3D"]
stream = ExtResource("2")
volume_db = -8.0
unit_size = 15.0
max_polyphony = 4
bus = &"SFX"
script = ExtResource("1")
P
cat > default_bus_layout.tres <<'P'
[gd_resource type="AudioBusLayout" format=3]

[resource]
bus/1/name = &"SFX"
bus/1/volume_db = 0.0
bus/1/send = &"Master"
P
cat > player.gd <<'P'
extends Node3D

@onready var _gun: Node = $Gun


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_gun.fire()
P
cat > enemy.gd <<'P'
extends Node3D

@onready var _gun: Node = $Gun


func _on_shoot_timer_timeout() -> void:
	_gun.fire()
P
cat > main.tscn <<'P'
[gd_scene load_steps=5 format=3]

[ext_resource type="Script" path="res://player.gd" id="1"]
[ext_resource type="Script" path="res://enemy.gd" id="2"]
[ext_resource type="PackedScene" path="res://gun.tscn" id="3"]

[sub_resource type="PlaneMesh" id="1"]
size = Vector2(80, 80)

[node name="Main" type="Node3D"]

[node name="Ground" type="MeshInstance3D" parent="."]
mesh = SubResource("1")

[node name="Player" type="Node3D" parent="."]
script = ExtResource("1")

[node name="Gun" parent="Player" instance=ExtResource("3")]

[node name="Enemy" type="Node3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, -35)
script = ExtResource("2")

[node name="Gun" parent="Enemy" instance=ExtResource("3")]

[node name="ShootTimer" type="Timer" parent="Enemy"]
wait_time = 1.5
autostart = true

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.5, 0.866, 0, -0.866, 0.5, 0, 12, 7)

[connection signal="timeout" from="Enemy/ShootTimer" to="Enemy" method="_on_shoot_timer_timeout"]
P
