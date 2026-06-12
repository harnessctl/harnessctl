---
name: game-design
description: Visual target generation, risk-first game decomposition, and verification criteria. Load at pipeline start before architecture.
---

# Game Design — Visual Target & Decomposition

## Overview

Two-phase design process that precedes all implementation:

1. **Visual Target** — generate a reference screenshot that anchors art direction
2. **Decomposition** — analyze risks, define verification criteria, produce a game plan spec (via `spec-create`)

---

## Phase 1: Visual Target

Generate a reference image of what the finished game looks like. Anchors art direction for scaffold, asset planner, and task agents.

### Generate

Use the `godot-asset-gen` tool:

```
godot-asset-gen image --model gemini --prompt "{prompt}" --size 1K --aspect-ratio 16:9 -o reference.png
```

### Prompt Rules

The reference must look like an **in-game screenshot**, not concept art. Every distinct object visible becomes an asset requirement downstream.

- **Enumerate every game object** — player, each enemy type, obstacles, collectibles, projectiles, platforms, props. Name each with position and approximate size. Objects absent from the reference get forgotten downstream.
- **Reflect real technical constraints** — tiling backgrounds should prompt tiling-friendly composition. Separate sprite layers should show distinct objects, not composited photorealism.
- **Do NOT prompt downgraded quality** ("lowpoly", "pixel art", "retro") — produces worse output. Prompt clean, sharp rendering with the actual composition needed.
- **Focus on the most important gameplay moment** — the frame showing spatial layout, core mechanic, and the camera perspective the player sees most.
- **Exclude what you will NOT build** — volumetric lighting, motion blur, depth of field, atmospheric fog, complex reflections, lens flares, detailed cast shadows. They create asset requirements nobody can fulfill.
- **Show HUD/UI elements** — health bar, score counter, minimap, inventory slots with screen positions. These are implementation requirements too.

### Prompt Template

```
Screenshot of a {2D/3D} video game. {Camera: angle, distance, perspective}.
Game objects: {player — appearance, position, size vs screen}. {enemies/NPCs — each type, position}. {obstacles}. {collectibles/pickups}. {projectiles if any}.
Environment: {background layers — sky, distant, mid}. {playfield surface — material, tiling}. {foreground elements}. {boundaries/edges}.
HUD: {each UI element — type and screen position}.
{Art style, color palette}. Clean sharp digital rendering, game engine output.
```

### Output

- `reference.png` — 1K 16:9 image
- Write art direction into a draft (via `draft-create`):

```markdown
# Assets

**Art direction:** <the art style description>
```

---

## Phase 2: Decomposition

Analyze the game for implementation risks and define verification criteria. Output is a game plan spec (created via `spec-create` with `type=task`).

### Workflow

1. **Read `reference.png`** — camera angle, scene complexity, entity count, environment scope.
2. **Read the game description** — core technical requirements.
3. **Scan for risks** — identify features needing isolation (see taxonomy).
4. **Define verification criteria** — risk-specific, general, and final.
5. **Write the game plan spec** (via `spec-create` with `type=task`, `author=game-director`).

### Risk Taxonomy

#### ISOLATE (fail unpredictably, ambiguous errors when mixed)

- **Procedural generation** — terrain, levels, meshes, dungeon layouts
- **Procedural animation** — runtime bone manipulation, IK, ragdoll blending
- **Sprite/character animations** — multi-direction movement, state transitions (almost always fail first pass)
- **Complex vehicle physics** — wheel colliders, suspension, drifting, motorcycle balance
- **Custom shaders** — water surfaces, portals, screen-space effects, dissolve/distortion
- **Runtime geometry** — destructible environments, CSG operations, mesh deformation
- **Dynamic navigation** — pathfinding adapting to runtime obstacles, crowd simulation, flocking
- **Complex camera systems** — third-person with collision avoidance, cinematic rail transitions, split-screen

#### NEVER ISOLATE (Godot handles well)

CharacterBody movement, collision/triggers, TileMap/GridMap, NavigationAgent on static navmesh, UI with Control nodes, spawning/timers/waves, camera follow, state machines, input handling.

### Verification Criteria

Each task gets a **Verify** field — what to check after implementation.

**Risk tasks** — target the exact failure mode:

- Animations: "every direction plays correct frames, transitions smooth, no pose snapping"
- Procedural gen: "output covers expected area, no gaps, no overlaps, no degenerate geometry"

**Main build** — combine cross-cutting with game-specific checks:

- Movement direction matches player input
- Animation direction matches movement direction
- Player input → character response feels correct
- Physics objects respond to gravity/collision
- UI readable, no overflow or overlap
- No missing textures (magenta/checkerboard)
- Game-specific checks (e.g., "enemies path around towers," "score increments on pickup")
- `reference.png` consistency
- Presentation video as final deliverable

### Game Plan Format

```markdown
# Game Plan: {Name}

## Game Description

{Original description, verbatim.}

## Risk Tasks

{Omit entirely if no risks identified.}

### 1. {Risk Feature}

- **Why isolated:** {what makes this algorithmically hard}
- **Verify:** {specific criteria targeting the failure mode}

## Main Build

{What to build — all routine systems. High-level, not implementation recipes.}

- **Assets needed:** {visual assets — type, approximate size, visual role. Omit if none.}
- **Verify:**
  - {General checks: movement/input/animation alignment, physics, UI, textures}
  - {Game-specific checks}
  - Gameplay flow matches game description
  - No visual glitches, clipping, or placeholder assets
  - reference.png consistency: color palette, scale, camera angle, visual density
  - **Presentation video:** ~30s cinematic MP4 showcasing gameplay
    - Write test/presentation.gd (SceneTree script), ~900 frames at 30 FPS
    - **3D:** smooth camera work, good lighting, post-processing
    - **2D:** camera pans, zoom transitions, tight viewport framing
    - Output: screenshots/presentation/gameplay.mp4
```

### What NOT to Include in the Game Plan

- GDScript code or implementation details
- Detailed technical specs
- Micro-tasks for routine features
- Untestable requirements
- Artificial boundaries between routine systems
