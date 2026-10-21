#!/usr/bin/env bash
set -e
bash "$(dirname "$0")/../_fixtures/enemies_json.sh"
cat > data/waves.csv <<'P'
time,kind,count
5,slime,3
20,bat,5
45,golem,1
P
cat > wave_spawner.gd <<'P'
extends Node

var waves: Array[PackedStringArray] = []

func _ready() -> void:
	var file := FileAccess.open("res://data/waves.csv", FileAccess.READ)
	file.get_csv_line()
	while not file.eof_reached():
		var row := file.get_csv_line()
		if row.size() == 3:
			waves.append(row)
P
