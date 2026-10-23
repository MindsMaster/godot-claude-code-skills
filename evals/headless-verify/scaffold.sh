#!/usr/bin/env bash
set -e
bash "$(dirname "$0")/../_fixtures/broken_player.sh"
# 评测沙箱只能访问工作目录
mkdir .bin
cp "${GODOT_BIN:-$(command -v godot)}" .bin/godot
cat >> project.godot <<'P'

[autoload]

Events="*res://events.gd"
P
cat > events.gd <<'P'
extends Node

@warning_ignore("unused_signal")
signal coin_collected(amount: int)
P
cat > hud.gd <<'P'
extends Label

var _coins: int = 0

func _ready() -> void:
	Events.coin_collected.connect(_on_coin_collected)

func _on_coin_collected(amount: int) -> void:
	_coins += amount
	text = str(_coins)
P
sed -i 's|^\[sub_resource|[ext_resource type="Script" path="res://hud.gd" id="2"]\n\n[sub_resource|' main.tscn
cat >> main.tscn <<'P'

[node name="Hud" type="Label" parent="."]
script = ExtResource("2")
P
mkdir enemies
cat > enemies/slime.gd <<'P'
extends CharacterBody2D

@export var speed := 60.0
@export var max_hp := 3

var hp := max_hp
var _stun_time := 0.0

func take_hit(damage: int, knockback: Vector2) -> void:
	hp -= damage
	velocity = knockback
	_stun_time = 0.3
	if hp <= 0:
		queue_free()

func heal_half() -> void:
	hp = max_hp * 0.5

func push(velocity: Vector2) -> void:
	position += velocity * 0.1

func _physics_process(_delta: float) -> void:
	if _stun_time > 0.0:
		return
	velocity.x = -speed
	move_and_slide()
P
sed -i 's|^\[sub_resource|[ext_resource type="Script" path="res://enemies/slime.gd" id="3"]\n\n[sub_resource|' main.tscn
cat >> main.tscn <<'P'

[node name="Slime" type="CharacterBody2D" parent="."]
script = ExtResource("3")
P
