#!/usr/bin/env bash
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "Forward Plus")
P
echo 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAKElEQVR4nGNgoCawiTrxH4Q/nFiAFcPkRw0gwgBCeNSAUQPwGkAOAAClzmg44Rx4QAAAAABJRU5ErkJggg==' | base64 -d > player.png
cat > main.tscn <<'P'
[gd_scene load_steps=3 format=3]

[sub_resource type="PlaneMesh" id="1"]
size = Vector2(20, 20)

[sub_resource type="BoxMesh" id="2"]

[node name="Main" type="Node3D"]

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.866, 0.5, 0, -0.5, 0.866, 0, 5, 8)

[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.707, 0.707, 0, -0.707, 0.707, 0, 6, 0)
shadow_enabled = true

[node name="Ground" type="MeshInstance3D" parent="."]
mesh = SubResource("1")
P
