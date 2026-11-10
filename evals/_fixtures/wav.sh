#!/usr/bin/env bash
# 用法 . wav.sh 后 wav <名字> <毫秒>  生成 48 kHz 单声道 16 位满幅白噪声
le32() {
	printf "\\x$(printf %02x $(($1 & 255)))\\x$(printf %02x $((($1 >> 8) & 255)))\\x$(printf %02x $((($1 >> 16) & 255)))\\x$(printf %02x $((($1 >> 24) & 255)))"
}

wav() {
	local bytes=$(($2 * 96))
	{
		printf 'RIFF'
		le32 $((bytes + 36))
		printf 'WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\xbb\x00\x00\x00\x77\x01\x00\x02\x00\x10\x00data'
		le32 "$bytes"
		head -c "$bytes" /dev/urandom
	} > "$1.wav"
}

project() {
	cat > project.godot <<P
config_version=5

[application]

config/name="Fixture"
run/main_scene="res://$1"
config/features=PackedStringArray("4.7", "Forward Plus")
P
}

# 用法 buses Music SFX UI
buses() {
	{
		printf '[gd_resource type="AudioBusLayout" format=3]\n\n[resource]\n'
		local i=1
		for name in "$@"; do
			printf 'bus/%d/name = &"%s"\nbus/%d/send = &"Master"\n' $i "$name" $i
			i=$((i + 1))
		done
	} > default_bus_layout.tres
}
