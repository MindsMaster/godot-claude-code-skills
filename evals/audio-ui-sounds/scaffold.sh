#!/usr/bin/env bash
set -e
. "$(dirname "$0")/../_fixtures/wav.sh"
project main_menu.tscn
buses Music SFX UI
wav hover 150
wav click 150
cat > main_menu.gd <<'P'
extends Control


func _ready() -> void:
	%Start.pressed.connect(_on_start_pressed)
	%Quit.pressed.connect(get_tree().quit)
	%Start.grab_focus()


func _on_start_pressed() -> void:
	get_tree().change_scene_to_file("res://game.tscn")
P
cat > main_menu.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://main_menu.gd" id="1"]

[node name="MainMenu" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1")

[node name="VBox" type="VBoxContainer" parent="."]
layout_mode = 0
offset_right = 200.0
offset_bottom = 120.0

[node name="Start" type="Button" parent="VBox"]
unique_name_in_owner = true
layout_mode = 2
text = "Start"

[node name="Options" type="Button" parent="VBox"]
unique_name_in_owner = true
layout_mode = 2
text = "Options"

[node name="Quit" type="Button" parent="VBox"]
unique_name_in_owner = true
layout_mode = 2
text = "Quit"
P
cat > pause_menu.gd <<'P'
extends CanvasLayer


func _ready() -> void:
	hide()
	%Resume.pressed.connect(toggle)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		toggle()


func toggle() -> void:
	get_tree().paused = not get_tree().paused
	visible = get_tree().paused
P
cat > pause_menu.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://pause_menu.gd" id="1"]

[node name="PauseMenu" type="CanvasLayer"]
process_mode = 3
script = ExtResource("1")

[node name="VBox" type="VBoxContainer" parent="."]
offset_right = 200.0
offset_bottom = 120.0

[node name="Resume" type="Button" parent="VBox"]
unique_name_in_owner = true
layout_mode = 2
text = "Resume"

[node name="Settings" type="Button" parent="VBox"]
unique_name_in_owner = true
layout_mode = 2
text = "Settings"
P
cat > game.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="PackedScene" path="res://pause_menu.tscn" id="1"]

[node name="Game" type="Node2D"]

[node name="PauseMenu" parent="." instance=ExtResource("1")]
P
