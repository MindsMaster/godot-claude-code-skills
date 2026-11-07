![godot-claude-code-skills](.github/banner.jpg)

# godot-claude-code-skills

[中文](README.md) | English

[![check](https://github.com/MindsMaster/godot-claude-code-skills/actions/workflows/check.yml/badge.svg)](https://github.com/MindsMaster/godot-claude-code-skills/actions/workflows/check.yml)
[![Godot](https://img.shields.io/badge/Godot-4.4%20~%204.7.2-478CBF?logo=godotengine&logoColor=white)](https://godotengine.org/)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-join-5865F2?logo=discord&logoColor=white)](https://discord.invite.azuramc.cc/)

A Claude Code plugin for Godot 4 with 18 skills. It directs Claude Code to the nodes, resources and project settings built into the engine and away from common misuse. Covers 2D, 3D, UI, animation, audio, data, shaders, editor extensions and headless testing, in GDScript and C#.

# Example

Skills load automatically from the request; there is no need to name one. Given the following request:

> Add a follow camera to the player. Smooth follow, never show anything outside the level, shake on damage. The player respawns at a checkpoint after falling into a pit, and the camera must be in place the moment the player respawns.

With `godot-2d` loaded, the implementation:

- Enables `position_smoothing_enabled` on `Camera2D` and bounds it to the level with `limit_*`
- Shakes through `offset`, with noise from `FastNoiseLite`
- Calls `reset_smoothing()` immediately after setting `global_position` in the respawn code

Other cases:

| Task | Built-in solution |
| --- | --- |
| Tile levels and digging | `TileMapLayer`, `TileSet` terrains, `set_cells_terrain_connect` |
| Designer-editable stat tables | Custom `Resource` saved as `.tres`, external sheets converted at import time |
| Health bar and HUD | `ProgressBar`, Container layout, project-wide `Theme` |
| 2D characters in a 3D scene | `Sprite3D` billboard with `alpha_cut` shadows |
| Ducking music under dialogue | `AudioEffectCompressor` on the bus with `sidechain` set to Voice |
| 3D sound effect muffled in game | Set `attenuation_filter_cutoff_hz` to 20500 instead of converting formats |
| Per-enemy hit flash on a shared material | `instance uniform` with `Tween` |

# Verification

- API: every class and member name in the text is checked against the class reference in the Godot engine source
- GDScript: every example runs in Godot 4.7.2, described behavior is verified with assertions, and rendering examples are rendered with software Vulkan and verified by reading pixels
- C#: every example compiles against Godot.NET.Sdk 4.7.2
- CI: all checks run on every push

Targets the latest stable release, 4.7.2, and supports 4.4 and later. APIs added in 4.5 or later are marked with their version.

The skill text is written in Chinese. Claude Code reads it directly and responds in the user's language. Code and identifiers are in English.

# Evaluation

Each case in `evals/` poses a development task and runs with and without the plugin installed. A run passes only when both hold:

- The result meets the task: an LLM judge checks it item by item, and afterwards every project is loaded in Godot 4.7.2 and C# projects are built
- The solution is clean: no script reimplements what the engine already provides, nothing that can be set once is recomputed every frame, no unrequested features are added, no unused code is left behind; no specific API is required

| Agent model | With | Without |
| --- | --- | --- |
| `claude-opus-5-5` | 14/17 | 6/17 |
| `claude-sonnet-5-5` | | |
| `claude-haiku-5-5` | | |

`claude-opus-5-5` per case, November 2026, Claude Code 2.1.319, judge model `claude-sonnet-5-5`. Each case ran once per condition; cases with a failure were topped up to 3 runs:

| Task | With | Without | Lines added with/without | Reason for failure |
| --- | --- | --- | --- | --- |
| Follow camera and respawn | 1/1 | 0/1 | 38 / 60 | Without: the level bounds are written both in the scene and in the script |
| 3D gunshot muffled up close, distance muffling kept far away | 1/1 | 1/1 | 0 / 0 | |
| Volume settings and ducking music under dialogue | 1/3 | 0/3 | 61 / 178 | Runs in both conditions add an unrequested audio manager or settings persistence; without the plugin, a script detects speech to duck the music |
| Category mix buses and sidechain ducking on monster attacks | 1/1 | 1/1 | 7 / 7 | |
| C# hit flash on a shared material | 1/1 | 0/1 | 22 / 28 | Without: the shader multiplies the texture twice, so unflashed colors are too dark |
| Pixel-art character in a 3D scene | 3/3 | 0/3 | 0 / 9 | Without: the feet float 1 pixel; 2 runs add a script that rotates the shadow every frame |
| Headless fixing of script errors and warnings | 1/1 | 1/1 | 0 / 0 | |
| Designer data and export | 0/1 | 1/1 | 76 / 54 | With: the same export setting is configured twice and an unused method is left behind |
| Tile level and digging | 3/3 | 1/3 | 13 / 30 | Without: in 2 runs the neighbor tiles do not update after digging |
| HUD and unified font | 1/1 | 0/1 | 19 / 20 | Without: the theme keeps unused font size styles |
| Thread pool keeps only two cores busy, count and results unchanged | 1/1 | 1/1 | 5 / 10 | |
| Total | 14/17 | 6/17 | | |

- Lines added: non-blank, non-comment lines in scripts and shaders minus the original project, averaged over runs
- With the plugin, all 17 runs loaded the matching skill
- The October 2026 result of 38/39 vs 6/39 used different grading and is not comparable

To reproduce:

```
claude plugin eval . --scaffold --trust-plugin --allow-tools Edit Write Bash \
  --model claude-opus-5-5 --judge-model claude-sonnet-5-5 \
  --threshold 0 --keep-temp --json evals/results/run.json
python3 evals/load_check.py evals/results/run.json
python3 evals/score.py evals/results/run.json
```

- Granting Bash requires `bubblewrap` and `socat`
- The headless case copies Godot from `GODOT_BIN`, `godot` on PATH, or `evals/_fixtures/bin/godot`
- `load_check.py` uses `GODOT_BIN` and `DOTNET_BIN` and needs the projects kept by `--keep-temp`
- A PATH entry on a slow mount, such as `/mnt/c` under WSL, makes the sandbox time out; trim PATH first

# Contents

| skill | Scope |
| --- | --- |
| `godot-builtin-first` | Entry point; looks for a built-in solution before writing a feature and routes to the specific skill |
| `godot-scene-architecture` | Scene composition, node references, signals, groups, autoloads, state machines, lifecycle |
| `godot-scene-authoring` | Placing new levels, backdrops, NPCs, props and UI in scenes, auditing whether a project authors content in scenes or builds it at runtime, generating tscn from scripts, self-drawing @tool nodes, keeping derived properties out of saves, exporting data for simulation on save, migration |
| `godot-gdscript` | Static typing, annotations, signals and await, warning settings |
| `godot-csharp` | Name mapping, source generators, StringName caching, lifecycle, hot reload |
| `godot-2d` | CharacterBody2D, TileMapLayer, Camera2D, Parallax2D, pixel art, 2D lighting |
| `godot-3d` | CharacterBody3D, physics engines, lighting and GI, import pipeline, LOD, skeleton modifiers |
| `godot-2d-in-3d` | Sprite3D billboards, alpha cut and shadows, SubViewport, HD-2D post-processing |
| `godot-ui` | Container layout, Theme, health bars, RichTextLabel, stretch modes, localization |
| `godot-animation` | AnimationPlayer, AnimationTree, Tween, SpriteFrames, deterministic playback |
| `godot-input` | InputMap actions, gamepads, deadzones, persisting rebinds |
| `godot-audio` | Bus layout, volume settings, category mixing and loudness, sidechain ducking, AudioStreamRandomizer, polyphony, dynamic music, import formats, 3D distance filter |
| `godot-resources-data` | Custom Resources, threaded loading, save data, import-time baking, built-in curve resources |
| `godot-shaders-vfx` | Shader parameters, instance uniforms, particles, Environment, post-processing, CompositorEffect |
| `godot-editor-tooling` | @tool, EditorPlugin, Inspector plugins, import plugins, undo, shortcuts |
| `godot-multiplayer` | ENet connections, RPC, Spawner and Synchronizer, late join, custom transports, prediction and correction, two-process acceptance |
| `godot-headless-testing` | Headless command line, smoke scenes, exit codes, CI, GUT, gdUnit4 |
| `godot-performance` | Profiler and Monitors, MultiMesh, physics interpolation, WorkerThreadPool, shader compilation stutter |

# Installation

Enabling the plugin per Godot project is recommended. At user scope, the 18 skill descriptions, about 4300 characters in total, enter the context of every turn in every project. Skill bodies load only when invoked.

Install at project scope from the Godot project directory:

```
claude plugin marketplace add MindsMaster/godot-claude-code-skills
claude plugin install godot-skills@godot-claude-code-skills --scope project
```

Omit `--scope project` to install at user scope.

To enable it for all members of a project, commit `.claude/settings.json` in that project:

```json
{
  "extraKnownMarketplaces": {
    "godot-claude-code-skills": {
      "source": {
        "source": "github",
        "repo": "MindsMaster/godot-claude-code-skills"
      }
    }
  },
  "enabledPlugins": {
    "godot-skills@godot-claude-code-skills": true
  }
}
```

It takes effect once a member opens the project and trusts the folder.

The marketplace must be added from the Git repository. When only the `marketplace.json` URL is given, the plugin's relative path `"source": "."` cannot be resolved.

# Updating

The plugin has no version number; each commit is a release. Third-party marketplaces do not auto-update by default. Choose one of the following:

- Manual: run `claude plugin update godot-skills@godot-claude-code-skills`, or open `/plugin` in a session, select the plugin under Installed and click Update now
- Automatic: open `/plugin` in a session, select `godot-claude-code-skills` under Marketplaces and click Enable auto-update. Updates are then checked within 10 minutes after the first message of each session

Run `/reload-plugins` or restart the session to apply an update.

# Contributing

Issues and pull requests are welcome. When reporting a mismatch between a skill and engine behavior, include the Godot version and a minimal reproduction.

Authoring rules are in `CLAUDE.md`. For local development, run `claude plugin marketplace add ./godot-claude-code-skills` against a local clone; each session reads the current files on startup.

Run the full test suite before submitting a pull request:

```
GODOT_BIN=/path/to/godot DOTNET_BIN=/path/to/dotnet python3 tests/check.py
```

The suite runs lint, api, gd, run and cs in order. run executes each GDScript example; the scenes, resources and calls an example requires are defined in the fixture file `tests/run/<skill>.md`. Error or warning output, failed assertions and timeouts count as failures. Rendering examples require `xvfb-run` and a Vulkan driver; install `mesa-vulkan-drivers` on machines without a GPU. See `tests/README.md` for details.

# Community

- Discord: <https://discord.invite.azuramc.cc/>
- QQ group: 1046048297

# License

MIT. See `LICENSE`.

Third-party material in the banner and icon:

- Background: screenshot of the Godot demo [tps-demo](https://github.com/godotengine/tps-demo) by Juan Linietsky and Fernando Miguel Calabró, licensed under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). Cropped, with a gradient overlay
- Godot logo: by Andrea Calabró, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Claude logo: a trademark of Anthropic

This project is not affiliated with Anthropic or the Godot Foundation.
