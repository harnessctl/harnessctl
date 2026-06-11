---
name: game-assets
description: Budget-aware asset planning, image/3D/animation generation, background removal. Load when generating or managing game assets.
---

# Game Assets — Planning, Generation & Processing

## Overview

Three-phase asset workflow:

1. **Plan** — analyze game, identify assets, budget allocation
2. **Generate** — create images, 3D models, animated sprites
3. **Process** — background removal, frame extraction, loop trimming

---

## Phase 1: Asset Planning

### Input

- `budget_cents` — total budget (or remaining for iterations)
- Game plan spec (in `.specs/`) — game description, risk tasks, main build with asset needs
- Architecture notes (draft in `.ai.tmp/`) — architecture with Asset Hints section
- `reference.png` — visual composition target
- Art direction notes (draft in `.ai.tmp/`) — art direction from visual target phase

### Workflow

1. **Read `reference.png`** — understand visual composition, proportions, environment layers.
2. **Read architecture Asset Hints + game plan Assets needed** — reconcile both lists (they may overlap or complement each other).
3. **Categorize assets:**
   - **3D models** — characters, vehicles, key props, buildings (need geometry)
   - **Textures** — ground, walls, UI backgrounds (flat, tileable)
   - **Backgrounds** — sky panoramas, parallax layers, title screens (large scenic)
   - **Animated sprites** — characters/objects with multiple actions (plan motion graph first)
4. **Budget allocation** (see cost table below).
5. **Identify anchors vs derivatives** — anchors generated first, derivatives use anchor as `--image` input.
6. **Generate, review, convert** — images in parallel, review PNGs, retry bad ones (max 1), convert approved 3D refs to GLBs.

### Cost Table

| Asset Type                 | Backend             | Cost               | Notes                           |
| -------------------------- | ------------------- | ------------------ | ------------------------------- |
| Texture / simple sprite    | Grok                | 2c                 | Fast, simple images             |
| Character / reference      | Gemini 1K           | 7c                 | Precise prompt following        |
| Background (simple)        | Grok                | 2c                 | Sky, clouds, abstract           |
| Background (precise)       | Gemini 2K           | 10c                | Specific layout/composition     |
| 3D model (full)            | Gemini 1K + GLB     | 47c                | 7c image + 40c GLB high quality |
| Animation reference        | Gemini 1K           | 7c                 | Once per character              |
| Animation action (root)    | Gemini pose + video | 7c + 5c x duration | From reference                  |
| Animation action (chained) | Video only          | 5c x duration      | From predecessor's last frame   |

Reserve ~10% of budget for retries. Prioritize by visual impact — cut low-impact assets first.

### Backend Selection

- **Gemini** (`--model gemini`) — reference images, character design, 3D model references, animated sprite refs/poses, backgrounds with precise layout. Costs more but reliably matches prompt.
- **Grok** (`--model grok`, default) — textures, simple objects, item kits, props, simple scenic backgrounds. High-quality but imprecise — great when exact prompt adherence doesn't matter.

### Art Direction Usage

Read the **Art direction** from your draft but do NOT mechanically prepend it. Different asset types need different treatment:

- **Textures** — often need no style language at all
- **3D model references** — need clean studio lighting; style cues can hurt mesh quality
- **Backgrounds** — benefit most from art direction language
- **Sprites** — some style cues, adapted to the subject

### Image References for Consistency

Feed a generated image as `--image` input when subsequent assets need to match it:

- **Style family** — one hero asset as input for the rest of the set
- **Multiple views** — front view as input for side, back, 3/4 angle
- **Variants** — base object as input for recolors, damaged versions, sizes
- **Scene coherence** — background as input for foreground props

Generate anchors first, review, then fan out derivatives in parallel.

---

## Phase 2: Generation CLI

All tools are TypeScript-based. Run from project root.

### Generate Image

```bash
godot-asset-gen image --prompt "the full prompt" -o assets/img/car.png
```

Options:

- `--model` (default `grok`): `grok` (2c), `gemini` (5-15c by size)
- `--size` (default `1K`): Grok: `1K`, `2K`. Gemini: `512`, `1K`, `2K`, `4K`
- `--aspect-ratio` (default `1:1`): `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`
- `--image` — reference image for image-to-image editing

Typical combos:

- `--model gemini --size 1K` — refs, characters, 3D refs (7c)
- `--model gemini --size 2K --aspect-ratio 16:9` — backgrounds (10c)
- `--model grok` — textures, simple objects (2c)

### Generate GLB (3D Model)

```bash
godot-asset-gen glb --image assets/img/car.png -o assets/glb/car.glb
```

Options:

- `--quality`: `default` (50c) or `high` (40c, HD textures)

Do NOT remove background before GLB conversion — Tripo3D needs the solid white bg.

### Generate Video (Animated Sprites)

```bash
godot-asset-gen video --prompt "walking right, smooth cycle" --image assets/img/pose.png --duration 2 -o assets/video/walk.mp4
```

Options:

- `--duration` (1-15 seconds)
- `--resolution` (default `720p`): `720p`, `480p` — always use 720p

### Set Budget

```bash
godot-asset-gen set_budget 500
```

Sets budget to 500 cents. Call once at start. All generations check remaining budget.

### Output Format

JSON to stdout: `{"ok": true, "path": "...", "cost_cents": 7}`
On failure: `{"ok": false, "error": "...", "cost_cents": 0}`

---

## Prompt Templates

### Background / Scenic Image

```
{description in the art style}. {composition instructions}.
```

`godot-asset-gen image --prompt "..." --size 2K --aspect-ratio 16:9 -o path.png`

### Texture (Tileable)

```
{name}, {description}. Top-down view, uniform lighting, no shadows, seamless tileable texture, suitable for game engine tiling, clean edges.
```

`godot-asset-gen image --prompt "..." -o path.png`

### Single Object / Sprite

**Simple (Grok):**

```
{name}, {description}. Centered on a solid {bg_color} background.
```

**Character (Gemini):**

```
{name}, {description}. Centered on a solid {bg_color} background.
```

`godot-asset-gen image --model gemini --prompt "..." -o path.png`

### Item Kit (Multiple Objects)

```
{item1}, {item2}, {item3}, {item4}. 2x2 grid layout, each item centered in its cell, solid {bg_color} background. {art style}.
```

Slice into individual PNGs:

```bash
godot-grid-slice path_grid.png -o assets/img/items/ --grid 2x2 --names "sword,shield,potion,helm"
```

### 3D Model Reference

```
3D model reference of {name}. {description}. 3/4 front elevated camera angle, solid white background, soft diffused studio lighting, matte material finish, single centered subject, no shadows on background. Any windows or glass should be solid tinted (opaque).
```

`godot-asset-gen image --model gemini --prompt "..." -o path.png`

Key: 3/4 front elevated angle, solid white/gray bg, matte finish, opaque glass, single subject.

### Animated Sprite

**Reference (Gemini 1K):**

```
{name}, {description}. Neutral standing pose, facing right, centered on a solid {bg_color} background. Clean silhouette.
```

**Pose (per action):**

```
{action pose description}, side view, solid {bg_color} background.
```

**Video (per action):**

```
{action}, smooth animation. Solid {bg_color} background.
```

---

## Phase 3: Processing

### Background Removal

Applies to: characters, props, icons, UI elements, animated sprite frames.
Does NOT apply to: textures, backgrounds, 3D model references.

**CRITICAL: Never prompt for "transparent background" — the generator draws a checkerboard. Always use a solid color background, then remove it.**

#### BG Color Strategy

Pick a color that is (1) **distinct from the subject** for clean mask separation, and (2) **close to the expected in-game environment** so residual fringe blends naturally.

Examples: forest → `dark-green`; sky/water → `steel-blue`; dungeon → `dark-gray`; generic → `medium-gray`.

Avoid pure chromakey (`#00FF00`) — creates unnatural fringing.

#### CLI

**Single image:**

```bash
godot-rembg assets/img/car.png -o assets/img/car_nobg.png --preview
```

**Batch (video frames):**

```bash
godot-rembg --batch frames_dir/ -o clean_dir/
```

#### Modes

`-m auto` (default) selects based on mask coverage:

| Mode    | When          | Behavior                                                    |
| ------- | ------------- | ----------------------------------------------------------- |
| `trust` | 5-70% mask fg | Keep all mask-fg pixels, aggressively remove bg             |
| `adapt` | >70% mask fg  | Adaptive threshold — fg pixels CAN be removed if bg-colored |
| `color` | <5% mask fg   | Color matting only, no mask — rough fallback                |

#### QA Verification

Always pass `--preview` — generates a `_qa.png` composited on contrasting solid color. Read the QA image to check for remnants, fringing, or missing foreground. Delete after inspection.

#### Fixing Results

- **Background remnants** → `--bg-thresh 0.03` (lower = more aggressive)
- **Missing foreground** → `-m trust` or `--fg-thresh 0.30` (higher = more protective)
- **Fringing** → `-m adapt --fg-thresh 0.10` + `--bg-thresh 0.03`. If persists, bg color too close to subject.
- **Mask failed** → result rough, regenerate source image

Tune `--bg-thresh` and `--fg-thresh` together. For batch: tune on one frame first.

### Frame Extraction

```bash
mkdir -p assets/video/knight_walk_frames
ffmpeg -i assets/video/knight_walk.mp4 -vsync 0 assets/video/knight_walk_frames/%04d.png
```

### Loop Detection (Looping Animations Only)

```bash
godot-loop-detect assets/video/knight_walk_frames/
```

Output: `{"loop_frame": 54, "similarity": 0.9983, "window": 7, "total_frames": 73}`

`window: 0` means no good loop point — use whole clip. Delete frames after loop point. Skip for one-shot animations (attack, death, jump).

### Grid Slicing (Item Kits)

```bash
godot-grid-slice path_grid.png -o assets/img/items/ --grid 2x2 --names "sword,shield,potion,helm"
```

---

## Asset Manifest Format

Track all assets in a draft (via `draft-create`). Every asset row **must** include a **Size** column — the intended in-game dimensions:

- **3D models:** target size in meters (e.g., `4m long`)
- **Textures:** tile size in meters (e.g., `2m tile`)
- **Backgrounds:** pixel dimensions (e.g., `1920x1080`)
- **Sprites:** display size in pixels (e.g., `128x128 px`)

```markdown
# Assets

**Art direction:** <the art direction string>

## 3D Models

| Name | Description        | Size    | Image              | GLB                |
| ---- | ------------------ | ------- | ------------------ | ------------------ |
| car  | sedan with spoiler | 4m long | assets/img/car.png | assets/glb/car.glb |

## Textures

| Name  | Description  | Size    | Image                |
| ----- | ------------ | ------- | -------------------- |
| grass | green meadow | 2m tile | assets/img/grass.png |

## Backgrounds

| Name      | Description  | Size                  | Image                    |
| --------- | ------------ | --------------------- | ------------------------ |
| forest_bg | dense forest | 1920x1080, fullscreen | assets/img/forest_bg.png |

## Sprites

| Name | Description        | Size     | Image               |
| ---- | ------------------ | -------- | ------------------- |
| coin | spinning gold coin | 64x64 px | assets/img/coin.png |

## Animated Sprites

### knight

**Reference:** `assets/img/knight_ref.png`
**Transitions:** idle <-> walk, walk -> attack -> idle

| Action | Type     | Size       | Duration | Start From | Frames Dir                |
| ------ | -------- | ---------- | -------- | ---------- | ------------------------- |
| idle   | loop     | 128x128 px | 2s       | ref        | assets/img/knight_idle/   |
| walk   | loop     | 128x128 px | 3s       | ref        | assets/img/knight_walk/   |
| attack | one-shot | 128x128 px | 2s       | walk       | assets/img/knight_attack/ |
```

**Start From:** `ref` = generate pose from reference. Action name = use that action's last extracted frame as video input.

**Generation order:** roots first (parallel) -> extract + loop trim -> chains (parallel) -> extract -> batch rembg all.

---

## Visual Pitfalls

### Direction and Orientation

Generators cannot reliably distinguish left vs right facing. Generate one direction only, flip in-game (`sprite.flip_h = true`). Verify with visual-qa.

### Video Size Consistency

Image assets (1024px) vs video frames (~720px): resize everything to the smallest source size before background removal. Downscale images to match video resolution.

### Animation Playback

Video frames are typically 24fps — set frame duration to `1.0/24 = 0.042s`. Don't reset frame counter between movement tiles.

### Common Mistakes

- **Detailed image shrunk to a tile** — 1024px downscaled to 64px looks muddy. Use 128px+ display, kit images, or prompt for bold simple forms.
- **Tiling texture for unique background** — use `--size 2K` scenic instead.
- **Image where code works** — pure geometry (solid rectangles, circles) should be drawn in code. Anything with texture/detail/artistic style should use generated assets.
- **Stretching texture** — small texture on large surface looks blurry. Use tileable or higher resolution.

### Image-to-Image Prompting

When `--image` is provided, the model sees the reference. Do NOT re-describe the character — focus on what's different (action, angle, change). Re-describing competes with the visual reference.
