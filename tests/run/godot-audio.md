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
