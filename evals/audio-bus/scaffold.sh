#!/usr/bin/env bash
set -e
bash "$(dirname "$0")/../_fixtures/platformer2d.sh"
for name in music jump line; do
	{
		printf 'RIFF\x24\x58\x01\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\xbb\x00\x00\x00\x77\x01\x00\x02\x00\x10\x00data\x00\x58\x01\x00'
		head -c 88064 /dev/urandom
	} > "$name.wav"
done
cat > npc.gd <<'P'
extends Node2D

@onready var _voice: AudioStreamPlayer = $Voice


# 对话系统在角色开口时调用
func speak(line: AudioStream) -> void:
	_voice.stream = line
	_voice.play()
P
cat > main.tscn <<'P'
[gd_scene load_steps=7 format=3]

[ext_resource type="Script" path="res://player.gd" id="1"]
[ext_resource type="Script" path="res://npc.gd" id="2"]
[ext_resource type="AudioStream" path="res://music.wav" id="3"]
[ext_resource type="AudioStream" path="res://jump.wav" id="4"]
[ext_resource type="AudioStream" path="res://line.wav" id="5"]

[sub_resource type="RectangleShape2D" id="1"]
size = Vector2(24, 40)

[node name="Main" type="Node2D"]

[node name="Music" type="AudioStreamPlayer" parent="."]
stream = ExtResource("3")
autoplay = true

[node name="Player" type="CharacterBody2D" parent="."]
script = ExtResource("1")

[node name="CollisionShape2D" type="CollisionShape2D" parent="Player"]
shape = SubResource("1")

[node name="JumpSound" type="AudioStreamPlayer" parent="Player"]
stream = ExtResource("4")

[node name="Npc" type="Node2D" parent="."]
position = Vector2(200, 0)
script = ExtResource("2")

[node name="Voice" type="AudioStreamPlayer" parent="Npc"]
stream = ExtResource("5")
P
