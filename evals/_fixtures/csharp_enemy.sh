#!/usr/bin/env bash
set -e
cat > project.godot <<'P'
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "C#", "Forward Plus")

[dotnet]

project/assembly_name="Fixture"
P
cat > Fixture.csproj <<'P'
<Project Sdk="Godot.NET.Sdk/4.7.2">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <EnableDynamicLoading>true</EnableDynamicLoading>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
P
cat > flash.gdshader <<'P'
shader_type canvas_item;

uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0);

void fragment() {
	vec4 base = texture(TEXTURE, UV);
	COLOR = vec4(mix(base.rgb, flash_color.rgb, flash), base.a);
}
P
cat > Enemy.cs <<'P'
using Godot;

public partial class Enemy : Sprite2D
{
	[Export]
	public int Health { get; set; } = 30;

	public void TakeDamage(int amount)
	{
		Health -= amount;
		if (Health <= 0)
		{
			QueueFree();
		}
	}
}
P
cat > main.tscn <<'P'
[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://Enemy.cs" id="1"]
[ext_resource type="Shader" path="res://flash.gdshader" id="2"]

[sub_resource type="ShaderMaterial" id="1"]
shader = ExtResource("2")
shader_parameter/flash = 0.0
shader_parameter/flash_color = Color(1, 1, 1, 1)

[node name="Main" type="Node2D"]

[node name="Enemy" type="Sprite2D" parent="."]
material = SubResource("1")
script = ExtResource("1")
P
