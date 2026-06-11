---
name: game-bootstrap
description: Godot 4 project scaffolding — project.godot, architecture notes, script stubs, scene builders, build order. Load after game decomposition.
---

# Game Bootstrap — Architecture & Scaffolding

Design game architecture and produce a compilable Godot project skeleton: `project.godot`, architecture notes (written to a draft via `draft-create`), script stubs, and scene builder stubs. Defines _what exists and how it connects_ — not behavior.

Works for both fresh projects and incremental changes.

## Workflow

1. **Read `reference.png`** — camera angle, distance, FOV, lighting, environment structure, scene layout. Informs node hierarchy, camera setup, lighting rig.
2. **Read input** — game description (fresh) or change request (incremental).
3. **Assess project state:**
   - No project → create from scratch.
   - Existing project, fresh start → delete existing scenes/scripts.
   - Existing project, incremental → read existing architecture notes and scripts. Identify what to add/replace. Preserve unchanged files.
4. **Design/update architecture** — scenes, scripts, signals, input actions.
5. **Write/update `project.godot`.**
6. **Write architecture notes** to the draft path — always complete, not a diff.
7. **Write script stubs** — for new scripts and explicitly replaced ones.
8. **Import assets** — `timeout 60 godot --headless --import 2>&1`. Ensures all assets (`.glb`, `.png`) are imported before scene builders reference them.
9. **Build scenes** — for each new/changed scene, write builder to `scenes/build_{name}.gd`, then run in dependency order (leaf scenes first): `timeout 60 godot --headless --script scenes/build_{name}.gd`

> **MCP alternative (when `godot_editor` is enabled — see `mcp-tools-godot` skill):** For trivial scenes (a root node + a few children, no complex transforms), use `create_scene` + `add_node` + `load_sprite` + `save_scene` instead of writing a scene builder script. For scenes with scripts attached, custom properties, precise transforms, or sub-scene instantiation — always use scene builder scripts. Use `godot_analyze_scene` from `godot_forge` to check `.tscn` files for antipatterns after building.

10. **Verify** — `timeout 60 godot --headless --quit 2>&1`. No `ERROR` or `Parser Error` lines. RID warnings are benign.
11. **Git commit** — `git add -A && git commit -m "scaffold: project skeleton"`

## Output Files

### 1. project.godot

```ini
; Engine configuration file
; Do not edit manually

[application]

config/name="{ProjectName}"
run/main_scene="res://scenes/main.tscn"

[display]

window/size/viewport_width=1280
window/size/viewport_height=720
window/stretch/mode="canvas_items"
window/stretch/aspect="expand"

[physics]

common/physics_ticks_per_second=120
common/physics_interpolation=true
; 3D only — omit for 2D projects:
3d/physics_engine="Jolt Physics"

[rendering]

; 3D games:
lights_and_shadows/directional_shadow/soft_shadow_filter_quality=3
anti_aliasing/quality/msaa_3d=2
; 2D pixel art (instead of above):
; textures/canvas_textures/default_texture_filter=0
; 2d/snap/snap_2d_transforms_to_pixel=true

[layer_names]

; Name collision layers used by the game:
2d_physics/layer_1="player"
2d_physics/layer_2="enemies"

[autoload]

; Singletons — asterisk prefix means script (not scene):
; GameManager="*res://scripts/game_manager.gd"

[input]

move_forward={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":87,"key_label":0,"unicode":119)]
}
```

**Key physical keycodes:** W=87, A=65, S=83, D=68, Up=4194320, Down=4194322, Left=4194319, Right=4194321, Space=32, Enter=4194309, Escape=4194305, Shift=4194325, Ctrl=4194326, Alt=4194328.

**Mouse buttons** use InputEventMouseButton with button_index (1=left, 2=right) and matching button_mask:

```ini
fire={
"deadzone": 0.2,
"events": [Object(InputEventMouseButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"button_mask":1,"position":Vector2(0,0),"global_position":Vector2(0,0),"factor":1.0,"button_index":1,"canceled":false,"pressed":true,"double_click":false)]
}
```

### 2. Architecture Notes (draft)

Complete architecture reference. Written to a draft path provided by the orchestrator. Always written in full, even for incremental updates.

```markdown
# {Project Name}

## Dimension: {2D or 3D}

## Input Actions

| Action       | Keys  |
| ------------ | ----- |
| move_forward | W, Up |
| jump         | Space |

## Scenes

### Main

- **File:** res://scenes/main.tscn
- **Root type:** Node3D
- **Children:** Player, Enemy

### Player

- **File:** res://scenes/player.tscn
- **Root type:** CharacterBody3D

## Scripts

### PlayerController

- **File:** res://scripts/player_controller.gd
- **Extends:** CharacterBody3D
- **Attaches to:** Player:Player
- **Signals emitted:** died, scored
- **Signals received:** HurtBox.area_entered -> \_on_hurt_entered
- **Instantiates:** Bullet

## Signal Map

- Player:HurtBox.area_entered -> PlayerController.\_on_hurt_entered
- Main:GoalArea.body_entered -> LevelManager.\_on_goal_reached

## Build Order

1. scenes/build_player.gd -> scenes/player.tscn
2. scenes/build_enemy.gd -> scenes/enemy.tscn
3. scenes/build_main.gd -> scenes/main.tscn (depends: player.tscn, enemy.tscn)

## Asset Hints

- Player character model (~1.8m tall humanoid)
- Ground texture (tileable grass, 2m repeat)
- Sky panorama (360-degree daytime sky)
```

The `## Build Order` section lists the exact build sequence. Follow it mechanically — do NOT infer or reorder.

### 3. .gitignore

```
.claude
CLAUDE.md
assets
screenshots
.godot
*.import
```

Create `screenshots/` with an empty `.gdignore` so Godot skips it:

```bash
mkdir -p screenshots && touch screenshots/.gdignore
```

### 4. Script Stubs (scripts/\*.gd)

```gdscript
extends CharacterBody3D
## res://scripts/player_controller.gd

signal died
signal scored

@export var speed: float = 7.0
@export var jump_velocity: float = -4.5

func _ready() -> void:
    pass

func _physics_process(delta: float) -> void:
    pass

func _on_hurt_entered(area: Area3D) -> void:
    pass
```

Correct `extends`, signal declarations, `@export` defaults, empty lifecycle and handler methods.

### 5. Scene Builder Stubs (scenes/build\_\*.gd)

```gdscript
extends SceneTree
## Scene builder — run: timeout 60 godot --headless --script scenes/build_<name>.gd

func _initialize() -> void:
    var root := ROOT_TYPE.new()     # REPLACE ROOT_TYPE
    root.name = "ROOT_NAME"         # REPLACE ROOT_NAME

    # SCRIPT — delete block if no script on root
    root.set_script(load("SCRIPT_PATH"))  # REPLACE SCRIPT_PATH

    # CHILDREN — delete block if none, duplicate per child
    var CHILD_VAR = load("CHILD_PATH").instantiate()  # REPLACE
    CHILD_VAR.name = "CHILD_NAME"                      # REPLACE
    root.add_child(CHILD_VAR)

    # SAVE
    _set_owners(root, root)
    var packed := PackedScene.new()
    packed.pack(root)
    ResourceSaver.save(packed, "OUTPUT_PATH")  # REPLACE
    print("Saved: OUTPUT_PATH")                # REPLACE
    quit(0)

func _set_owners(node: Node, owner: Node) -> void:
    for c in node.get_children():
        c.owner = owner
        if c.scene_file_path.is_empty():
            _set_owners(c, owner)
```

**CRITICAL:** Use `=` (not `:=`) for `instantiate()` calls. The template uses `=` — do NOT change it.

## UI Overlay Architecture

```
Main (Node3D or Node2D)
+-- ... game nodes ...
+-- CanvasLayer (layer=1)
    +-- Control (anchors_preset=15, full rect)
        +-- VBoxContainer / HBoxContainer
        |   +-- Label (score)
        |   +-- ProgressBar (health)
        |   +-- Button (pause)
        +-- ...
```

**Layout containers:**

- `VBoxContainer` — vertical; `HBoxContainer` — horizontal
- `GridContainer` — grid (set `columns`); `MarginContainer` — padding
- `CenterContainer` — centering; `PanelContainer` — with background
- `size_flags_horizontal/vertical = 3` (SIZE_EXPAND_FILL)
- `custom_minimum_size` for fixed dimensions

For pause menus, set `process_mode = Node.PROCESS_MODE_ALWAYS` on the CanvasLayer.

## Architecture Rules

1. **Explicit 2D or 3D** — never mix dimensions in the same hierarchy.
2. **Declare all input actions** — anything used by scripts must appear in input table and project.godot.
3. **Signal contracts** — if script A emits signal X, receivers must list it in the signal map.

## Common Built-in Signals

- Area2D/3D — body_entered, body_exited, area_entered, area_exited
- Button — pressed
- Timer — timeout
- AnimationPlayer — animation_finished
- RigidBody2D/3D — body_entered (contact_monitor required)

## Common Errors

- **`Cannot infer the type of "x" variable`** — `:=` with `load().instantiate()`. Use `=` not `:=`.
- **`preload()` fails in headless** — always use `load()` in scene builders.
- **Scene builder hangs** — missing `quit()` call.

## Asset Hints in Architecture Notes

Include `## Asset Hints` listing what visual assets the architecture needs. The asset planner uses these.

Be specific about type (model, texture, background, sprite), approximate size, and visual role. Do NOT describe style — the asset planner chooses that.

## What NOT to Include

- Implementation details or behavior descriptions
- Task ordering
- Lighting, environment, tonemapping, post-processing
- Any logic beyond empty method stubs
