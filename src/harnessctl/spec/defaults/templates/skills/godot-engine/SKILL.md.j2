---
name: godot-engine
description: Godot 4 engine quirks, known bugs, workarounds, scene builder patterns, and material/lighting setup. Load before writing GDScript that interacts with the engine.
---

# Godot Engine — Quirks & Scene Generation

## Two Script Types

GDScript files in this pipeline fall into two categories. Confusing them is a major bug source.

### Scene Builders (build-time, headless)

- `extends SceneTree` with `_initialize()` entry point
- Run via `godot --headless --script build_scene.gd`
- Build node hierarchy, set owners, pack, validate, save `.tscn`, then `quit()`
- Do NOT use: `@onready`, `preload()`, signal connections, `look_at()`, `to_global()`
- `_process()` signature: `func _process(delta: float) -> bool:` (returns bool, not void)

### Runtime Scripts (game logic)

- `extends Node2D/3D`, `CharacterBody3D`, etc.
- Use `_ready()`, `_process()`, `_physics_process()`, signals, `@onready`
- Attached to scene nodes via `set_script()` in builders or editor

## Known Quirks

### Headless / Scene Builder Specific

- **RID leak errors on exit** — headless builders always produce these. Harmless; ignore.
- **`add_to_group()` in builders** — groups set at build-time persist in saved `.tscn` files.
- **`_ready()` skipped in `_initialize()`** — `_ready()` on instantiated scene nodes does NOT fire during `_initialize()`. Call init methods manually after `root.add_child()`.
- **Autoloads in SceneTree scripts** — cannot reference autoload singletons by name (compile error). Find via `root.get_children()` and match by `.name`.
- **`preload()` vs `load()` during generation** — do NOT use `preload()` for scenes/resources that may not exist yet. Use `load()`.
- **No spatial methods in `_initialize()`** — `look_at()`, `to_global()` fail because nodes aren't in the tree yet. Use `rotation_degrees` or compute transforms manually.

### Serialization

- **MultiMeshInstance3D + GLBs** — does NOT render after pack+save (mesh resource reference lost). Use individual GLB instances instead.
- **GLB `material_override` doesn't serialize** — setting `material_override` on GLB-internal MeshInstance3D nodes does NOT persist in `.tscn` because `set_owner_on_new_nodes()` skips GLB children. Use procedural ArrayMesh when custom material is required.
- **MultiMeshInstance3D `Mesh.duplicate()`** — needed before freeing the source GLB instance, otherwise the mesh resource is garbage-collected.

### Physics

- **`free()` vs `queue_free()` in test harnesses** — `queue_free()` leaves the node in `root.get_children()` until frame end, blocking name reuse. Use `free()` when immediately replacing scenes.
- **BoxShape3D on trimesh** — snags on collision edges (Godot/Jolt bug). Use CapsuleShape3D for objects that slide across trimesh surfaces.
- **Default collision mask misses non-default layers** — new bodies get `collision_mask = 1`. If terrain/walls use layer 2+, player falls through. Always set mask to include all needed layers.
- **Collision layer bitmask vs UI index** — `collision_layer`/`collision_mask` are bitmasks. UI Layer 1 = bitmask 1, Layer 2 = bitmask 2, Layer 3 = bitmask 4, Layer 4 = bitmask 8 (powers of 2).
- **Collision state changes in callbacks** — changing `.disabled` inside `body_entered`/`body_exited` → "Can't change state while flushing queries". Use `set_deferred("disabled", false)`.
- **`CharacterBody3D.MOTION_MODE_FLOATING`** — needed for non-platformer 3D movement (vehicles, snowboards). GROUNDED mode's `floor_stop_on_slope` fights slope movement.
- **`reset_physics_interpolation()`** — call when teleporting or switching cameras to prevent interpolation glitch.
- **2D collision shape sizing** — slightly smaller than tile (e.g., 48px in 64px grid) allows smooth cornering through 1-tile corridors.

### Camera

- **Camera2D has no `current` property** — use `make_current()`, only after node is in scene tree.
- **Camera lerp from origin** — cameras using `lerp()` in `_physics_process()` will swoop from (0,0,0) on first frame. Use an `_initialized` flag to snap position on first frame, then lerp.
- **Chase camera `current` re-assertion** — game cameras that set `current = true` in `_physics_process()` override the test harness camera every frame. Test harnesses must disable the game camera EVERY frame.

### Video/Movie Writer

- **`--write-movie` frame 0** — first frame renders before `_process()` runs. Camera position set in `_process()` won't appear until frame 1. Pre-position camera in `_initialize()` via `position`/`rotation_degrees` (NOT `look_at()`).
- **`await` during `--write-movie`** — `await get_tree().process_frame` advances the movie frame counter each tick. Use `_init_frames` counter in `_physics_process()` instead of await chains.

### Visual / Material

- **Frame-rate dependent drag** — `speed *= (1 - drag)` per tick is exponential decay tied to tick rate. Use `speed *= exp(-rate * delta)` for frame-rate independent damping.
- **ProceduralSkyMaterial sun disc** — uses DirectionalLight3D direction/color. Set `sky_mode = SKY_MODE_LIGHT_AND_SKY` on sun, `SKY_MODE_LIGHT_ONLY` on fill lights — otherwise multiple sun discs appear.
- **Smooth yaw tracking 360 spin** — `lerp()` on raw angles causes 360-degree spin-arounds. Wrap difference to [-PI, PI]: `var diff: float = fmod(target_yaw - current_yaw + 3.0 * PI, TAU) - PI`.
- **`StandardMaterial3D` with `no_depth_test = true` + `TRANSPARENCY_ALPHA`** → invisible. Use opaque + unshaded for overlays.
- **Z-fighting** between layered surfaces: offset 0.15-0.30m vertically + `render_priority = 1`.
- **`cull_mode = CULL_DISABLED`** as safety net on all procedural meshes until winding is confirmed correct.
- **UV tiling double-scaling** — do NOT use world-space UV coords AND `uv1_scale` together. Pick one.
- **MultiMeshInstance3D `custom_aabb`** — must cover the entire visible area. Without it, the MultiMesh gets frustum-culled when the camera moves to edges.
- **MultiMeshInstance3D materials** — has no `set_surface_override_material()`. Use `material_override` or keep materials from source mesh.

### Timing / Signals

- **Sibling signal timing in `_ready()`** — `_ready()` fires on children in tree order. If sibling A emits in its `_ready()`, sibling B hasn't connected yet. Fix: after connecting, check if the emitter already has data and call the handler manually.
- **`get_path()` is a built-in Node method** — returns NodePath. Cannot override. Name yours `get_track_path()`, `get_road_path()`, etc.
- **Spawn immunity for revealed items** — items spawned inside an active Area2D get `area_entered` immediately → destroyed same frame. Track `_alive_time` in `_process()`, ignore `area_entered` for ~0.8s.

## Type Inference Errors

Three common issues — applies in both scene builders and runtime scripts:

```gdscript
# WRONG — load() returns Resource, no instantiate():
var scene := load("res://assets/glb/car.glb")
var model := scene.instantiate()  # Error

# WRONG — := with instantiate() causes Variant inference error:
var scene: PackedScene = load("res://assets/glb/car.glb")
var model := scene.instantiate()  # Error

# CORRECT — type load() AND use = (not :=) for instantiate():
var scene: PackedScene = load("res://assets/glb/car.glb")
var model = scene.instantiate()  # Works

# WRONG — := with polymorphic math functions (return Variant):
var x := abs(speed)              # Error
# Affected: abs, sign, clamp, min, max, floor, ceil, round, lerp,
#   smoothstep, move_toward, wrap, snappedf, randf_range, randi_range

# WRONG — := with array/dictionary element access (returns Variant):
var pos := positions[i]          # Error

# CORRECT — explicit type or untyped:
var pos: Vector3 = positions[i]  # OK
var val = my_dict["key"]         # OK (untyped)
```

## Pass-by-Value Pitfall

`bool`, `int`, `float`, `Vector3`, `AABB`, `Transform3D` etc. are value types — assigning to a parameter inside a function does NOT update the caller:

```gdscript
# WRONG — result never updates caller:
func collect(node: Node, result: AABB) -> void:
    result = result.merge(child_aabb)  # lost at return

# CORRECT — use Array accumulator:
func collect(node: Node, out: Array) -> void:
    out.append(child_aabb)
```

## Scene Builder Template

```gdscript
extends SceneTree

func _initialize() -> void:
    print("Generating: {scene_name}")

    var root := {RootNodeType}.new()
    root.name = "{SceneName}"

    # ... build node hierarchy ...

    set_owner_on_new_nodes(root, root)

    var count := _count_nodes(root)
    var packed := PackedScene.new()
    var err := packed.pack(root)
    if err != OK:
        push_error("Pack failed: " + str(err))
        quit(1)
        return
    if not validate_packed_scene(packed, count, "res://{output_path}.tscn"):
        quit(1)
        return

    err = ResourceSaver.save(packed, "res://{output_path}.tscn")
    if err != OK:
        push_error("Save failed: " + str(err))
        quit(1)
        return

    print("BUILT: %d nodes" % count)
    quit(0)

func set_owner_on_new_nodes(node: Node, scene_owner: Node) -> void:
    for child in node.get_children():
        child.owner = scene_owner
        if child.scene_file_path.is_empty():
            set_owner_on_new_nodes(child, scene_owner)
        # else: instantiated scene (GLB/TSCN) — don't recurse

func _count_nodes(node: Node) -> int:
    var total := 1
    for child in node.get_children():
        total += _count_nodes(child)
    return total

func validate_packed_scene(packed: PackedScene, expected_count: int, scene_path: String) -> bool:
    var test_instance = packed.instantiate()
    var actual := _count_nodes(test_instance)
    test_instance.free()
    if actual < expected_count:
        push_error("Pack validation failed for %s: expected %d nodes, got %d" % [scene_path, expected_count, actual])
        return false
    return true
```

## Owner Chain (CRITICAL)

Call `set_owner_on_new_nodes(root, root)` ONCE at the end, after ALL `add_child()` calls.

**GLB OWNERSHIP BUG** — Never recurse unconditionally. If you recurse into instantiated GLB models, ALL internal mesh/material nodes get serialized inline, causing 100MB+ `.tscn` files. The template's `scene_file_path.is_empty()` check prevents this.

**WRONG patterns:**

```gdscript
# WRONG: Setting owner only on direct children
terrain.owner = root  # Terrain's children have NO owner!

# WRONG: Calling helper on containers instead of root
set_owner_on_new_nodes(track_container, root)  # track_container itself has NO owner!
```

## Common Node Compositions

**3D Physics Object:**

```gdscript
var body := RigidBody3D.new()
var collision := CollisionShape3D.new()
var mesh := MeshInstance3D.new()
var shape := BoxShape3D.new()
shape.size = Vector3(1, 1, 1)
collision.shape = shape
body.add_child(collision)
body.add_child(mesh)
```

**Script Attachment:**

```gdscript
var script := load("res://scripts/player_controller.gd")
player_node.set_script(script)
```

**3D Model Loading (GLB):**

```gdscript
var model_scene: PackedScene = load("res://assets/glb/car.glb")
var model = model_scene.instantiate()
model.name = "CarModel"

# Measure for scaling
var mesh_inst: MeshInstance3D = find_mesh_instance(model)
var aabb: AABB = mesh_inst.get_aabb() if mesh_inst else AABB(Vector3.ZERO, Vector3.ONE)
var target_length := 2.0
var scale_factor: float = target_length / aabb.size.x
model.scale = Vector3.ONE * scale_factor
model.position.y = -aabb.position.y * scale_factor

func find_mesh_instance(node: Node) -> MeshInstance3D:
    if node is MeshInstance3D:
        return node
    for child in node.get_children():
        var found = find_mesh_instance(child)
        if found:
            return found
    return null
```

**GLB orientation:** Imported models often face the wrong axis. Check AABB longest dimension to determine facing axis. If it doesn't match movement direction, rotate accordingly.

**Collision for imported models:** Always use simple primitives (BoxShape3D, SphereShape3D, CapsuleShape3D). Never use `create_convex_shape()`/`create_trimesh_shape()` on high-poly GLBs — causes <1 FPS.

## Environment & Lighting (3D)

```gdscript
# WorldEnvironment
var world_env := WorldEnvironment.new()
var env := Environment.new()
env.background_mode = Environment.BG_SKY
env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
env.ambient_light_color = Color.WHITE
env.ambient_light_sky_contribution = 0.5
var sky := Sky.new()
sky.sky_material = ProceduralSkyMaterial.new()
env.sky = sky
world_env.environment = env
root.add_child(world_env)

# Sun (DirectionalLight3D)
var sun := DirectionalLight3D.new()
sun.shadow_enabled = true
sun.shadow_bias = 0.05
sun.shadow_blur = 2.0
sun.directional_shadow_max_distance = 30.0
sun.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_AND_SKY
sun.rotation_degrees = Vector3(-45, -30, 0)
root.add_child(sun)
```

## CSG for Rapid Prototyping

```gdscript
var floor := CSGBox3D.new()
floor.size = Vector3(20, 0.5, 20)
floor.use_collision = true
floor.material = ground_mat
root.add_child(floor)

# Subtraction:
var hole := CSGCylinder3D.new()
hole.operation = CSGShape3D.OPERATION_SUBTRACTION
hole.radius = 1.0
hole.height = 1.0
floor.add_child(hole)
```

## Noise/Procedural Textures

```gdscript
var noise := FastNoiseLite.new()
noise.noise_type = FastNoiseLite.TYPE_CELLULAR
noise.frequency = 0.02
noise.fractal_type = FastNoiseLite.FRACTAL_FBM
noise.fractal_octaves = 5

var tex := NoiseTexture2D.new()
tex.noise = noise
tex.width = 1024
tex.height = 1024
tex.seamless = true
tex.as_normal_map = true
tex.bump_strength = 2.0
```

## StandardMaterial3D Extended

Beyond basic albedo:

- `normal_enabled = true` + `normal_texture` + `normal_scale = 2.0`
- `rim_enabled = true` + `rim_tint = 1.0` — silhouette glow
- `emission_enabled = true` + `emission_texture` — self-illumination
- `texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC`

## Scene Constraints Checklist

- [ ] `extends SceneTree` (not Node/Node2D/Node3D)
- [ ] `_initialize()` as entry, `quit()` at end
- [ ] `set_owner_on_new_nodes(root, root)` called ONCE after all `add_child()`
- [ ] `validate_packed_scene()` before `ResourceSaver.save()`
- [ ] No `@onready`, no `preload()`, no signal connections
- [ ] No `look_at()` / `to_global()` in `_initialize()`
- [ ] No 2D/3D mixing in same hierarchy
- [ ] `load()` typed as `PackedScene` for GLB/TSCN, `=` (not `:=`) for `instantiate()`
- [ ] Simple collision primitives for imported models

## Feedback Loop

Quirks are curated in this skill. When the task executor discovers a workaround during a game build, it writes to the knowledge graph (`memory` tools). Recurring patterns get promoted here by the skill maintainer.
