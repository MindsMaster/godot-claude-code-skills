#!/usr/bin/env bash
set -e
. "$(dirname "$0")/../_fixtures/wav.sh"
project title.tscn
buses Music SFX
wav title 8000
wav level 8000
wav boss 8000
cat > title.gd <<'P'
extends Control


func start_game() -> void:
	get_tree().change_scene_to_file("res://level_1.tscn")
P
cat > level.gd <<'P'
extends Node2D

@export_file("*.tscn") var next_scene: String


func finish() -> void:
	get_tree().change_scene_to_file(next_scene)
P
cat > title.tscn <<'P'
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://title.gd" id="1"]
[ext_resource type="AudioStream" path="res://title.wav" id="2"]

[node name="Title" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1")

[node name="Music" type="AudioStreamPlayer" parent="."]
stream = ExtResource("2")
autoplay = true
P
scene() {
	cat > "$1.tscn" <<P
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://level.gd" id="1"]
[ext_resource type="AudioStream" path="res://$2.wav" id="2"]

[node name="$3" type="Node2D"]
script = ExtResource("1")
next_scene = "res://$4.tscn"

[node name="Music" type="AudioStreamPlayer" parent="."]
stream = ExtResource("2")
autoplay = true
P
}
scene level_1 level Level1 level_2
scene level_2 level Level2 boss
scene boss boss Boss title
