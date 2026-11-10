#!/usr/bin/env bash
set -e
. "$(dirname "$0")/../_fixtures/wav.sh"
project game.tscn
buses Music SFX UI
wav music 8000
wav hum 8000
wav click 150
cat > pause_menu.gd <<'P'
extends CanvasLayer

@onready var _click: AudioStreamPlayer = $"../UiClick"


func _ready() -> void:
	hide()
	%Resume.pressed.connect(toggle)
	%Settings.pressed.connect(_click.play)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		toggle()


func toggle() -> void:
	get_tree().paused = not get_tree().paused
	visible = get_tree().paused
P
cat > game.tscn <<'P'
[gd_scene load_steps=5 format=3]

[ext_resource type="AudioStream" path="res://music.wav" id="1"]
[ext_resource type="AudioStream" path="res://hum.wav" id="2"]
[ext_resource type="AudioStream" path="res://click.wav" id="3"]
[ext_resource type="Script" path="res://pause_menu.gd" id="4"]

[node name="Game" type="Node2D"]

[node name="Camera2D" type="Camera2D" parent="."]

[node name="Music" type="AudioStreamPlayer" parent="."]
stream = ExtResource("1")
autoplay = true
bus = &"Music"

[node name="Machine" type="Node2D" parent="."]
position = Vector2(60, 0)

[node name="Hum" type="AudioStreamPlayer2D" parent="Machine"]
stream = ExtResource("2")
autoplay = true
bus = &"SFX"

[node name="UiClick" type="AudioStreamPlayer" parent="."]
stream = ExtResource("3")
bus = &"UI"

[node name="PauseMenu" type="CanvasLayer" parent="."]
process_mode = 3
script = ExtResource("4")

[node name="VBox" type="VBoxContainer" parent="PauseMenu"]
offset_right = 200.0
offset_bottom = 120.0

[node name="Resume" type="Button" parent="PauseMenu/VBox"]
unique_name_in_owner = true
layout_mode = 2
text = "Resume"

[node name="Settings" type="Button" parent="PauseMenu/VBox"]
unique_name_in_owner = true
layout_mode = 2
text = "Settings"
P
