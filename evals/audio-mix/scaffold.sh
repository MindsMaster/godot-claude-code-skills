#!/usr/bin/env bash
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "Forward Plus")
P
for name in gun monster_attack click wind music; do
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
bus/2/name = &"Music"
bus/2/volume_db = 0.0
bus/2/send = &"Master"
P
cat > gun.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="AudioStream" path="res://gun.wav" id="1"]

[node name="Gun" type="AudioStreamPlayer3D"]
stream = ExtResource("1")
max_polyphony = 6
attenuation_filter_cutoff_hz = 20500.0
bus = &"SFX"
P
cat > monster.gd <<'P'
extends Node3D

@onready var _attack_sound: AudioStreamPlayer3D = $AttackSound


func attack() -> void:
	_attack_sound.play()
P
cat > monster.tscn <<'P'
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://monster.gd" id="1"]
[ext_resource type="AudioStream" path="res://monster_attack.wav" id="2"]

[node name="Monster" type="Node3D"]
script = ExtResource("1")

[node name="AttackSound" type="AudioStreamPlayer3D" parent="."]
stream = ExtResource("2")
attenuation_filter_cutoff_hz = 20500.0
P
cat > wind.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="AudioStream" path="res://wind.wav" id="1"]

[node name="Wind" type="AudioStreamPlayer"]
stream = ExtResource("1")
volume_db = -12.0
autoplay = true
P
cat > music.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="AudioStream" path="res://music.wav" id="1"]

[node name="Music" type="AudioStreamPlayer"]
stream = ExtResource("1")
autoplay = true
bus = &"Music"
P
cat > hud.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="AudioStream" path="res://click.wav" id="1"]

[node name="Hud" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0

[node name="ClickSound" type="AudioStreamPlayer" parent="."]
stream = ExtResource("1")
bus = &"SFX"
P
cat > settings.gd <<'P'
extends VBoxContainer

@onready var _music: HSlider = $Music
@onready var _sfx: HSlider = $Sfx


func _ready() -> void:
	_bind(_music, &"Music")
	_bind(_sfx, &"SFX")


func _bind(slider: HSlider, bus_name: StringName) -> void:
	var bus := AudioServer.get_bus_index(bus_name)
	slider.value = AudioServer.get_bus_volume_linear(bus)
	slider.value_changed.connect(func(linear: float) -> void: AudioServer.set_bus_volume_linear(bus, linear))
P
cat > settings.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://settings.gd" id="1"]

[node name="Settings" type="VBoxContainer"]
script = ExtResource("1")

[node name="Music" type="HSlider" parent="."]
max_value = 1.0
step = 0.01
value = 1.0

[node name="Sfx" type="HSlider" parent="."]
max_value = 1.0
step = 0.01
value = 1.0
P
cat > main.tscn <<'P'
[gd_scene load_steps=7 format=3]

[ext_resource type="PackedScene" path="res://gun.tscn" id="1"]
[ext_resource type="PackedScene" path="res://monster.tscn" id="2"]
[ext_resource type="PackedScene" path="res://wind.tscn" id="3"]
[ext_resource type="PackedScene" path="res://music.tscn" id="4"]
[ext_resource type="PackedScene" path="res://hud.tscn" id="5"]
[ext_resource type="PackedScene" path="res://settings.tscn" id="6"]

[node name="Main" type="Node3D"]

[node name="Gun" parent="." instance=ExtResource("1")]

[node name="Monster" parent="." instance=ExtResource("2")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, -10)

[node name="Wind" parent="." instance=ExtResource("3")]

[node name="Music" parent="." instance=ExtResource("4")]

[node name="Hud" parent="." instance=ExtResource("5")]

[node name="Settings" parent="Hud" instance=ExtResource("6")]

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.5, 0.866, 0, -0.866, 0.5, 0, 12, 7)
P
