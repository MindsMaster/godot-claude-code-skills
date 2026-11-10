#!/usr/bin/env bash
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "Forward Plus")
P
for name in explore combat; do
	{
		printf 'RIFF\x24\x58\x01\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\xbb\x00\x00\x00\x77\x01\x00\x02\x00\x10\x00data\x00\x58\x01\x00'
		head -c 88064 /dev/urandom
	} > "$name.wav"
	cat > "$name.wav.import" <<P
[remap]

importer="wav"
type="AudioStreamWAV"

[deps]

source_file="res://$name.wav"

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
done
cat > default_bus_layout.tres <<'P'
[gd_resource type="AudioBusLayout" format=3]

[resource]
bus/1/name = &"Music"
bus/1/volume_db = 0.0
bus/1/send = &"Master"
P
cat > music.gd <<'P'
extends Node


func enter_combat() -> void:
	pass


func exit_combat() -> void:
	pass
P
cat > main.tscn <<'P'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://music.gd" id="1"]

[node name="Main" type="Node"]

[node name="Music" type="Node" parent="."]
script = ExtResource("1")
P
