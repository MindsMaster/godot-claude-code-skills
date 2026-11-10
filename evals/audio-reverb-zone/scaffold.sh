#!/usr/bin/env bash
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "Forward Plus")
P
for name in roar torch; do
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
cat > enemy.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="AudioStream" path="res://roar.wav" id="1"]

[node name="Enemy" type="Node3D"]

[node name="Roar" type="AudioStreamPlayer3D" parent="."]
stream = ExtResource("1")
bus = &"SFX"
P
cat > torch.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="AudioStream" path="res://torch.wav" id="1"]

[node name="Torch" type="Node3D"]

[node name="Crackle" type="AudioStreamPlayer3D" parent="."]
stream = ExtResource("1")
autoplay = true
bus = &"SFX"
P
cat > main.tscn <<'P'
[gd_scene load_steps=4 format=3]

[ext_resource type="PackedScene" path="res://enemy.tscn" id="1"]
[ext_resource type="PackedScene" path="res://torch.tscn" id="2"]

[sub_resource type="BoxShape3D" id="1"]
size = Vector3(30, 10, 30)

[node name="Main" type="Node3D"]

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2, 40)

[node name="CaveZone" type="Area3D" parent="."]

[node name="CollisionShape3D" type="CollisionShape3D" parent="CaveZone"]
shape = SubResource("1")

[node name="EnemyInCave" parent="." instance=ExtResource("1")]

[node name="TorchInCave" parent="." instance=ExtResource("2")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 5, 0, 0)

[node name="EnemyOutside" parent="." instance=ExtResource("1")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 60, 0, 0)
P
