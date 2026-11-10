#!/usr/bin/env bash
# 触发率用例共用的小工程 玩家 敌人 音乐 设置菜单
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "Forward Plus")
P
for name in gun music click step; do
	{
		printf 'RIFF\x24\x58\x01\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\xbb\x00\x00\x00\x77\x01\x00\x02\x00\x10\x00data\x00\x58\x01\x00'
		head -c 88064 /dev/urandom
	} > "$name.wav"
done
cat > player.gd <<'P'
extends CharacterBody2D

@export var speed := 220.0

@onready var _gun: AudioStreamPlayer2D = $Gun
@onready var _anim: AnimatedSprite2D = $Sprite


func _physics_process(_delta: float) -> void:
	velocity = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down") * speed
	move_and_slide()
	if Input.is_action_just_pressed("ui_accept"):
		_gun.play()


func take_damage(_amount: int) -> void:
	_anim.play("hurt")
P
cat > options.gd <<'P'
extends Control

@onready var _music: HSlider = %MusicSlider
@onready var _sfx: HSlider = %SfxSlider
P
cat > options.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://options.gd" id="1"]

[node name="Options" type="Control"]
layout_mode = 3
anchors_preset = 15
script = ExtResource("1")

[node name="VBox" type="VBoxContainer" parent="."]
layout_mode = 0

[node name="MusicSlider" type="HSlider" parent="VBox"]
unique_name_in_owner = true
layout_mode = 2

[node name="SfxSlider" type="HSlider" parent="VBox"]
unique_name_in_owner = true
layout_mode = 2

[node name="Back" type="Button" parent="VBox"]
layout_mode = 2
text = "Back"
P
cat > main.tscn <<'P'
[gd_scene load_steps=6 format=3]

[ext_resource type="Script" path="res://player.gd" id="1"]
[ext_resource type="AudioStream" path="res://gun.wav" id="2"]
[ext_resource type="AudioStream" path="res://music.wav" id="3"]
[ext_resource type="PackedScene" path="res://options.tscn" id="4"]

[sub_resource type="SpriteFrames" id="1"]
animations = [{"frames": [], "loop": true, "name": &"hurt", "speed": 5.0}]

[node name="Main" type="Node2D"]

[node name="Player" type="CharacterBody2D" parent="."]
script = ExtResource("1")

[node name="Sprite" type="AnimatedSprite2D" parent="Player"]
sprite_frames = SubResource("1")

[node name="Gun" type="AudioStreamPlayer2D" parent="Player"]
stream = ExtResource("2")

[node name="Music" type="AudioStreamPlayer" parent="."]
stream = ExtResource("3")
autoplay = true

[node name="UI" type="CanvasLayer" parent="."]

[node name="Options" parent="UI" instance=ExtResource("4")]
visible = false
P
