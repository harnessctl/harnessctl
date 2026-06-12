---
name: game-execution
description: Task implementation workflow, test harnesses, screenshot/video capture, visual debugging. Load before implementing game tasks.
---

# Game Execution — Implementation, Testing & Capture

## Phases

### Risk Tasks (if game plan has any)

Implement each risk feature in isolation before the main build:

1. Set up minimal environment — only the nodes needed to exercise the risk
2. Run the implementation loop until the risk task's **Verify** criteria pass
3. Commit

### Main Build

Implement everything in the game plan's **Main Build**:

1. Generate scenes first, then scripts (scenes create nodes that scripts attach to)
2. Run the implementation loop until verification criteria pass
3. Run final verification including presentation video
4. Commit

---

## Implementation Loop

1. **Import assets** — `timeout 60 godot --headless --import` (generates `.import` files — without this, `load()` fails). Re-run after modifying assets.
2. **Generate scenes** — write scene builder scripts, compile to `.tscn`
3. **Generate scripts** — write `.gd` files
4. **Pre-validate** — `timeout 30 godot --headless --check-only -s <path>` for each new/modified `.gd`
5. **Validate project** — `timeout 60 godot --headless --quit 2>&1`
6. **Fix errors** — if validation fails, fix and re-validate
7. **Capture** — write test harness, run with `--write-movie`, produce screenshots
8. **Verify** — check captures against verification criteria + `reference.png` consistency. Check stdout for `ASSERT FAIL`.
9. **Visual QA** — delegate to Heimdall (visual-qa subagent) when applicable
10. If verification fails → fix and repeat from step 2

> **MCP alternative (when `godot_editor` is enabled — see `mcp-tools-godot` skill):** For step 5, use `run_project` + `get_debug_output` instead of `godot --headless --quit` for interactive validation with richer console output. Use `stop_project` to terminate. For pre-validation (step 4), use `get_diagnostics` from `godot_diagnostics` for LSP-level checks. Steps 1 and 7 have no MCP equivalent — always use bash for asset import and `--write-movie` capture.

After each phase: update the game plan spec status, write discoveries to knowledge graph (`memory` tools), git commit.

### Iteration Tracking

There is no fixed iteration limit — use judgment:

- If there is progress (even small iterative steps) — keep going
- If you recognize a **fundamental limitation** (wrong architecture, missing engine feature) — stop early, even after 2-5 iterations
- Stop signal: "making the same kind of fix repeatedly without convergence"

---

## Commands

```bash
# Import new/modified assets (MUST run before scene builders):
timeout 60 godot --headless --import

# Compile a scene builder (produces .tscn):
timeout 60 godot --headless --script <path_to_builder.gd>

# Pre-validate a single script:
timeout 30 godot --headless --check-only -s <path_to_script.gd>

# Validate all project scripts:
timeout 60 godot --headless --quit 2>&1
```

**Common errors:**

- `Parser Error` — syntax error, fix the line indicated
- `Invalid call` / `method not found` — wrong node type or API, delegate to Mimir for class lookup
- `Cannot infer type` — `:=` used with `instantiate()` or polymorphic math functions
- Script hangs — missing `quit()` in scene builder

---

## Test Harnesses

Write `test/test_{task_id}.gd` — a SceneTree script that loads the scene under test and verifies the task's goal. Do NOT call `quit()` — the movie writer handles exit.

### Contract

```gdscript
extends SceneTree

func _initialize() -> void:
    # Setup: load scene, position camera, configure test
    var scene: PackedScene = load("res://scenes/main.tscn")
    var root_scene = scene.instantiate()
    root.add_child(root_scene)

    # Camera must be activated explicitly
    var cam := Camera3D.new()
    cam.position = Vector3(0, 5, 10)
    cam.current = true
    root.add_child(cam)

func _process(delta: float) -> bool:
    # Return false to keep running
    return false
```

### Console Assertions

Use `print("ASSERT PASS/FAIL: ...")` for behavioral properties hard to judge visually (positions, velocities, state changes). After capture, check stdout for `ASSERT FAIL` lines.

### Simulated Input

```gdscript
var timer := Timer.new()
timer.wait_time = 1.0
timer.one_shot = true
timer.timeout.connect(func(): Input.action_press("move_forward"))
root.add_child(timer)
timer.start()
```

### Sustained Movement (Presentations)

Open-loop input (timed press/release) doesn't work for 30-second videos — per-frame errors compound. Use **closed-loop waypoint steering** based on actual position each frame.

---

## Capture

### Setup (Cross-Platform)

Detects platform, timeout command, GPU availability. Defines `run_godot` wrapper for all platform differences.

```bash
PLATFORM=$(uname -s)

# Timeout command
if command -v timeout &>/dev/null; then
    TIMEOUT_CMD="timeout"
elif command -v gtimeout &>/dev/null; then
    TIMEOUT_CMD="gtimeout"
else
    timeout_fallback() { perl -e 'alarm shift; exec @ARGV' "$@"; }
    TIMEOUT_CMD="timeout_fallback"
fi

# Platform-specific Godot launcher
GPU_AVAILABLE=false
if [[ "$PLATFORM" == "Darwin" ]]; then
    GPU_AVAILABLE=true
    run_godot() { godot --rendering-method forward_plus "$@" 2>&1; }
elif [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "MSYS"* ]] || [[ "$PLATFORM" == "CYGWIN"* ]]; then
    # Windows — assume GPU available
    GPU_AVAILABLE=true
    run_godot() { godot --rendering-method forward_plus "$@" 2>&1; }
else
    # Linux — probe for GPU display
    for sock in /tmp/.X11-unix/X*; do
        d=":${sock##*/X}"
        if DISPLAY=$d $TIMEOUT_CMD 2 glxinfo 2>/dev/null | grep -qi nvidia; then
            GPU_AVAILABLE=true
            eval "run_godot() { DISPLAY=$d godot --rendering-method forward_plus \"\$@\" 2>&1; }"
            break
        fi
    done
    if ! $GPU_AVAILABLE; then
        run_godot() { xvfb-run -a -s '-screen 0 1280x720x24' godot --rendering-driver vulkan "$@" 2>&1; }
    fi
fi
```

When `GPU_AVAILABLE` is true — real shadows, SSR, SSAO, glow, volumetric fog. Without GPU — software rasterizer via lavapipe.

### Screenshot Capture

```bash
MOVIE=screenshots/{task_folder}
rm -rf "$MOVIE" && mkdir -p "$MOVIE"
touch screenshots/.gdignore
$TIMEOUT_CMD 30 run_godot \
    --write-movie "$MOVIE"/frame.png \
    --fixed-fps 10 --quit-after {N} \
    --script test/test_task.gd
```

**Frame rate and duration:**

- **Static scenes** (decoration, terrain, UI): `--fixed-fps 1`. Adjust `--quit-after` for number of views.
- **Dynamic scenes** (physics, movement): `--fixed-fps 10`. Low FPS breaks physics (delta too large → tunneling). Typical: 3-10s (30-100 frames).

### Video Capture

Requires hardware rendering. Skip if `GPU_AVAILABLE` is false.

```bash
if $GPU_AVAILABLE; then
    VIDEO=screenshots/presentation
    rm -rf "$VIDEO" && mkdir -p "$VIDEO"
    touch screenshots/.gdignore
    $TIMEOUT_CMD 60 run_godot \
        --write-movie "$VIDEO"/output.avi \
        --fixed-fps 30 --quit-after 900 \
        --script test/presentation.gd
    # Convert AVI (MJPEG) to MP4 (H.264)
    ffmpeg -i "$VIDEO"/output.avi \
        -c:v libx264 -pix_fmt yuv420p -crf 28 -preset slow \
        -vf "scale='min(1280,iw)':-2" \
        -movflags +faststart \
        "$VIDEO"/gameplay.mp4 2>&1
else
    echo "No GPU available — skipping video capture"
fi
```

CRF 28 + `-preset slow` targets ~2-5MB for 30s at 720p. `-movflags +faststart` enables streaming preview.

---

## Visual Debugging

### Isolate and Capture

Do NOT debug in a complex scene — isolate the problem:

1. **Minimal repro scene** — write `test/debug_{issue}.gd` with only the relevant nodes. Strip everything else.
2. **Targeted frames** — for animation/motion issues, capture at `--fixed-fps 10` for 3-5 seconds. Single frames cannot show timing bugs.
3. **Before/after** — capture with and without the fix. Ask "What changed between these two sets?"

### Animation Failures

Animations are the #1 source of silent failures — they "work" (no errors) but produce wrong results.

Common issues to probe (always capture multi-frame):

- **Frozen pose** — "Does the character's pose change between frames?"
- **Wrong animation** — "Describe how limbs/body move. Does it look like walking, idling, attacking?"
- **No blending** — "Are there sudden pose jumps between consecutive frames?"
- **AnimationPlayer vs AnimationTree conflicts** — both controlling same skeleton
- **Animation on wrong node** — targeting different skeleton path
- **Bone/track mismatches** — animation made for different model

### 3D Object Not Visible

Run this checklist in order:

1. **Exists?** — `print(node.name, " at ", node.global_position)` in `_ready()`. No output = not in tree.
2. **Debug marker** — emissive sphere (bright color, 0.5m) at object position. Visible = mesh/material problem. Not visible = camera problem.
3. **Camera direction** — `print(camera.global_position, camera.global_transform.basis.z)`. Force `camera.look_at(object.global_position)`.
4. **Occlusion** — hide large geometry (`terrain.visible = false`).
5. **Scale** — `print(node.scale)`. Too small (0.001) = sub-pixel. Too large = camera inside.
6. **Material** — transparency alpha=0 = invisible. Set `albedo_color = Color.RED` temporarily.

### Other Debug Scenarios

- **Node visibility** — hidden by z-order, wrong layer, zero alpha, off-camera, wrong viewport
- **Physics not working** — "Do any objects move due to gravity or collision?" (collision shapes likely missing)
- **UI layout** — "Are UI elements overlapping, cut off, or outside visible area?"
- **Shader/material** — "Are any surfaces showing magenta, checkerboard, or default grey?"

### Debug Scene Pattern

In `test/debug_{issue}.gd`:

1. Load only relevant nodes
2. Frame the issue with positioned camera
3. Add visible markers (colored boxes, labels) for position confirmation
4. Run enough frames to capture behavior
5. Feed to visual-qa question mode

---

## Project Memory

Read the knowledge graph (`memory` tools) before starting work — it contains discoveries from previous tasks. After completing your task, write back:

- What worked and what failed
- Technical specifics later tasks will need
- Workarounds discovered
