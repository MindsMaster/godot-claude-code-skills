#!/usr/bin/env bash
set -e
. "$(dirname "$0")/../_fixtures/wav.sh"
project main.tscn
buses Music SFX UI
wav music 8000
wav growl 8000
wav click 150
cat > enemy.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="AudioStream" path="res://growl.wav" id="1"]

[node name="Enemy" type="Node2D"]

[node name="Growl" type="AudioStreamPlayer2D" parent="."]
stream = ExtResource("1")
autoplay = true
max_distance = 400.0
bus = &"SFX"
P
cat > game.tscn <<'P'
[gd_scene load_steps=3 format=3]

[ext_resource type="AudioStream" path="res://music.wav" id="1"]
[ext_resource type="PackedScene" path="res://enemy.tscn" id="2"]

[node name="Game" type="Node2D"]

[node name="Player" type="Node2D" parent="."]

[node name="Camera2D" type="Camera2D" parent="Player"]

[node name="Enemy" parent="." instance=ExtResource("2")]
position = Vector2(60, 0)

[node name="Music" type="AudioStreamPlayer" parent="."]
stream = ExtResource("1")
autoplay = true
bus = &"Music"
P
cat > main.tscn <<'P'
[gd_scene load_steps=3 format=3]

[ext_resource type="PackedScene" path="res://game.tscn" id="1"]
[ext_resource type="AudioStream" path="res://click.wav" id="2"]

[node name="Main" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0

[node name="View" type="SubViewportContainer" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
stretch = true
stretch_shrink = 4

[node name="GameView" type="SubViewport" parent="View"]
handle_input_locally = false
canvas_item_default_texture_filter = 0
size = Vector2i(288, 162)
render_target_update_mode = 4

[node name="Game" parent="View/GameView" instance=ExtResource("1")]

[node name="Hud" type="CanvasLayer" parent="."]

[node name="Menu" type="Button" parent="Hud"]
offset_right = 80.0
offset_bottom = 31.0
text = "Menu"

[node name="Click" type="AudioStreamPlayer" parent="Hud"]
stream = ExtResource("2")
bus = &"UI"
P
