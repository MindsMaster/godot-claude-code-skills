# godot-audio

## SKILL.md `func _on_value_changed`

<!-- check: setup -->
```gdscript
AudioServer.add_bus()
AudioServer.set_bus_name(AudioServer.bus_count - 1, "Music")
```

```gdscript
await frames(2)
var bus := AudioServer.get_bus_index("Music")
node.value = 0.25
expect(is_equal_approx(AudioServer.get_bus_volume_linear(bus), 0.25), "音量跟随滑条")
node.value = 0.0
expect(AudioServer.is_bus_mute(bus), "滑到 0 静音")
```

## SKILL.md `AudioStreamRandomizer.new`

<!-- check: setup -->
```gdscript
node.hits = [make_tone(), make_tone(0.1)]
```

```gdscript
await frames(2)
var random := node.stream as AudioStreamRandomizer
expect(random.streams_count == 2, "两条音效都进了随机器")
node.play()
await frames(30)
```

## SKILL.md `AudioStreamPolyphonic.new`

<!-- check: setup -->
```gdscript
AudioServer.add_bus()
AudioServer.set_bus_name(AudioServer.bus_count - 1, "SFX")
```

```gdscript
await frames(2)
var first := node.play_sfx(make_tone())
var second := node.play_sfx(make_tone(), -6.0)
expect(first != AudioStreamPlaybackPolyphonic.INVALID_ID and second != first, "两个音效同时播放")
await frames(30)
```

## SKILL.md `func song_time`

<!-- check: setup -->
```gdscript
node.stream = make_tone(1.0)
```

```gdscript
await frames(2)
node.play()
await wait_real(0.4)
var first: float = node.song_time()
await wait_real(0.2)
var second: float = node.song_time()
expect(first > 0.0, "播放后歌曲时间为正")
expect(second > first, "歌曲时间随播放前进")
```

## references/dynamic-music.md `func enter_combat`

<!-- check: setup -->
```gdscript
var music := AudioStreamInteractive.new()
music.clip_count = 2
music.set_clip_name(0, &"Explore")
music.set_clip_stream(0, make_tone(1.0))
music.set_clip_name(1, &"Combat")
music.set_clip_stream(1, make_tone(1.0))
music.add_transition(AudioStreamInteractive.CLIP_ANY, AudioStreamInteractive.CLIP_ANY, AudioStreamInteractive.TRANSITION_FROM_TIME_IMMEDIATE, AudioStreamInteractive.TRANSITION_TO_TIME_START, AudioStreamInteractive.FADE_DISABLED, 0.0)
node.stream = music
```

```gdscript
node.play()
await frames(5)
node.enter_combat()
await wait_real(0.2)
var playback := node.get_stream_playback() as AudioStreamPlaybackInteractive
expect(playback.get_current_clip_index() == 1, "切到 Combat")
node.enter_explore()
await wait_real(0.2)
expect(playback.get_current_clip_index() == 0, "切回 Explore")
```

## references/dynamic-music.md `AudioStreamInteractive.new`

<!-- check: setup -->
```gdscript
node.explore = make_tone(1.0)
node.combat = make_tone(1.0)
```

## references/dynamic-music.md `func set_intensity`

<!-- check: setup -->
```gdscript
node.base_layer = make_tone(1.0)
node.drums_layer = make_tone(1.0)
```

```gdscript
await frames(5)
node.set_intensity(true)
expect(is_zero_approx((node.stream as AudioStreamSynchronized).get_sync_stream_volume(1)), "鼓点层打开")
await frames(5)
```

## SKILL.md `_gun.attenuation_filter_cutoff_hz = 20500.0`

<!-- check: setup -->
```gdscript
var noise := AudioStreamWAV.new()
noise.format = AudioStreamWAV.FORMAT_16_BITS
noise.mix_rate = 44100
noise.loop_mode = AudioStreamWAV.LOOP_FORWARD
noise.loop_end = 44100
var data := PackedByteArray()
data.resize(44100 * 2)
var rng := RandomNumberGenerator.new()
rng.seed = 7
for i in range(0, data.size(), 2):
	data.encode_s16(i, rng.randi_range(-12000, 12000))
noise.data = data
AudioServer.add_bus()
var probe := AudioServer.bus_count - 1
AudioServer.set_bus_name(probe, "Probe")
AudioServer.add_bus_effect(probe, AudioEffectSpectrumAnalyzer.new())
var gun := node.get_node("Gun") as AudioStreamPlayer3D
gun.stream = noise
gun.bus = &"Probe"
var camera := Camera3D.new()
camera.position = Vector3(0, 0, 14)
camera.current = true
node.add_child(camera)
```

```gdscript
var gun := node.get_node("Gun") as AudioStreamPlayer3D
var spectrum := AudioServer.get_bus_effect_instance(AudioServer.get_bus_index("Probe"), 0) as AudioEffectSpectrumAnalyzerInstance
gun.play()
await wait_real(0.5)
var high_off := spectrum.get_magnitude_for_frequency_range(8000, 16000).length()
var low_off := spectrum.get_magnitude_for_frequency_range(200, 1000).length()
gun.attenuation_filter_cutoff_hz = 5000.0
await wait_real(0.5)
var high_on := spectrum.get_magnitude_for_frequency_range(8000, 16000).length()
var low_on := spectrum.get_magnitude_for_frequency_range(200, 1000).length()
print("high off %.5f on %.5f low off %.5f on %.5f" % [high_off, high_on, low_off, low_on])
expect(high_off > 0.0 and high_on < high_off * 0.1, "volume_db -8 时默认滤波把 8 kHz 以上压掉 20 dB 以上")
expect(low_on > low_off * 0.7, "低频基本不受影响")
gun.volume_db = 0.0
await wait_real(0.5)
var high_full := spectrum.get_magnitude_for_frequency_range(8000, 16000).length()
expect(high_full > high_on * 5.0, "volume_db 回到 0 dB 滤波基本不生效")
```

## SKILL.md `duck.sidechain = &"Voice"`

<!-- check: setup -->
```gdscript
for bus_name: String in ["Music", "Voice"]:
	AudioServer.add_bus()
	AudioServer.set_bus_name(AudioServer.bus_count - 1, bus_name)
```

```gdscript
var music := AudioServer.get_bus_index(&"Music")
var music_player := AudioStreamPlayer.new()
music_player.bus = &"Music"
music_player.stream = make_tone(4.0)
node.add_child(music_player)
music_player.play()
await wait_real(0.5)
var alone := AudioServer.get_bus_peak_volume_left_db(music, 0)
var voice := AudioStreamPlayer.new()
voice.bus = &"Voice"
voice.stream = make_tone(3.0)
node.add_child(voice)
voice.play()
await wait_real(0.6)
var ducked := AudioServer.get_bus_peak_volume_left_db(music, 0)
var compressor := AudioServer.get_bus_effect(music, 0) as AudioEffectCompressor
compressor.threshold = 0.0
await wait_real(0.8)
var default_threshold := AudioServer.get_bus_peak_volume_left_db(music, 0)
print("alone %.1f ducked %.1f default threshold %.1f" % [alone, ducked, default_threshold])
expect(alone - ducked > 2.5 and alone - ducked < 6.0, "-12 dBFS 的语音把音乐压低约 4 dB")
expect(absf(alone - default_threshold) < 0.5, "threshold 0 dB 时完全不压")
```

## references/mixing.md `func _process`

<!-- check: setup -->
```gdscript
for bus_name: String in ["Music", "MonsterAttack"]:
	AudioServer.add_bus()
	AudioServer.set_bus_name(AudioServer.bus_count - 1, bus_name)
```

```gdscript
var duck := AudioServer.get_bus_effect(AudioServer.get_bus_index(&"Music"), 0) as AudioEffectAmplify
var attack := AudioStreamPlayer.new()
attack.bus = &"MonsterAttack"
attack.stream = make_tone(0.6)
node.add_child(attack)
attack.play()
await wait_real(0.4)
expect(is_equal_approx(duck.volume_db, -3.0), "出招时压到 -3 dB")
await wait_real(1.2)
expect(is_zero_approx(duck.volume_db), "出招结束后放回 0 dB")
```
