# LorQB — Agent & Subagent Roles

## Project identity
**LorQB (Lord of the Quantum Balls)** — Blender 3D animation project.
A ball travels through a chain of 4 hollow colored cubes (Blue, Red, Green, Yellow)
linked by hinges. Scripts drive all animation — no manual Blender UI steps.

AI development team: **Rukmini Trio** (Claude + ChatGPT + NotebookLM)
Lead developer: Carlos | Original design: Jose R. Velazquez (2014)
Repo: `cogaston0/lorqb-blender` | Branch: `claude/organize-lorqb-skills-3UOBD`

---

## Master component table

### C10 — Construction only (special case, no movement)

| Component   | Name                       | Responsibility                                      |
|-------------|----------------------------|-----------------------------------------------------|
| Skill       | `/lorqb-c10-scene-build`   | Knowledge doc: topology, params, constraints        |
| Artifact    | `C10_scene_build.py`       | Builds scene: cubes, ball, hinges, seats            |
| Agent       | `scene-geometry`           | Creates hollow cubes, holes, materials, ball        |
| Subagent 1  | `hinge-pivot`              | Places hinge empties, sets cube pivot origins       |
| Subagent 2  | `panel-ui`                 | Registers Build/Reset buttons in N-panel            |

---

### C Series — Movement only (C12 → C13 → C14 → C15)

Each C-series movement script dissects into the same 4 components:

| Component   | C12                        | C13                        | C14                          | C15                          |
|-------------|----------------------------|----------------------------|------------------------------|------------------------------|
| Transition  | Blue → Red                 | Red → Green                | Green → Yellow               | Yellow → Blue                |
| Skill       | `/lorqb-c12-blue-to-red`   | `/lorqb-c13-red-to-green`  | `/lorqb-c14-green-to-yellow` | `/lorqb-c15-yellow-to-blue`  |
| Artifact    | `C12_blue_to_red.py`       | `C13_red_to_green.py`      | `C14_green_to_yellow.py`     | `C15_yellow_to_blue.py`      |
| Agent       | `animation-keyframe`       | `animation-keyframe`       | `animation-keyframe`         | `animation-keyframe`         |
| Subagent 1  | `rotation-phase`           | `rotation-phase`           | `rotation-phase`             | `rotation-phase`             |
| Subagent 2  | `ball-transfer`            | `ball-transfer`            | `ball-transfer`              | `ball-transfer`              |
| Subagent 3  | `hinge-verify`             | `hinge-verify`             | `hinge-verify`               | `hinge-verify`               |

---

### T Series — Movement only (T01 → T02 → T03 → T04)

Same structure as C series — different cube pairs, same subagent anatomy:

| Component   | T01                        | T02                        | T03                        | T04                        |
|-------------|----------------------------|----------------------------|----------------------------|----------------------------|
| Transition  | Blue → Green               | Yellow → Red               | Red → Yellow               | Green → Blue               |
| Skill       | `/lorqb-t01-blue-to-green` | `/lorqb-t02-yellow-to-red` | `/lorqb-t03-red-to-yellow` | `/lorqb-t04-green-to-blue` |
| Artifact    | `T01_blue_to_green.py`     | `T02_yellow_to_red.py`     | `T03_red_to_yellow.py`     | `T04_green_to_blue.py`     |
| Agent       | `animation-keyframe`       | `animation-keyframe`       | `animation-keyframe`       | `animation-keyframe`       |
| Subagent 1  | `rotation-phase`           | `rotation-phase`           | `rotation-phase`           | `rotation-phase`           |
| Subagent 2  | `ball-transfer`            | `ball-transfer`            | `ball-transfer`            | `ball-transfer`            |
| Subagent 3  | `hinge-verify`             | `hinge-verify`             | `hinge-verify`             | `hinge-verify`             |

---

## Subagent definitions

### `scene-geometry`
Handles: cube shape, hole sizes, material colors, transparency
Primary file: `C10_scene_build.py`
Spawn when: changing cube dimensions, hole configs, ball radius, colors

### `hinge-pivot`
Handles: hinge empty placement, cube origin/pivot reassignment
Primary files: `C10` (placement), `C12–C15` (verification)
Spawn when: cubes detached, wrong pivot, hinge position incorrect

### `panel-ui`
Handles: Blender operator/panel registration, N-panel buttons
Primary files: `C01_lorQB_Master_Runner.py`, `C10` panel section
Spawn when: adding buttons, class conflicts, registration errors

### `animation-keyframe` (agent — orchestrates movement)
Handles: full movement sequence, rotation angles, frame timing
Primary files: `C12–C15`, `T01–T04`
Coordinates: `rotation-phase` + `ball-transfer` + `hinge-verify`

### `rotation-phase` (subagent of animation-keyframe)
Handles: cube rotation keyframes, axis constraints, angle values
Spawn when: cube overshoots, wrong rotation axis, easing issues

### `ball-transfer` (subagent of animation-keyframe)
Handles: ball parent swap (cube → hinge → next cube), seat landing
Spawn when: ball misses seat, wrong swap frame, parent chain breaks

### `hinge-verify` (subagent of animation-keyframe)
Handles: confirms hinge is correctly placed before animation runs
Spawn when: pre-flight check before any movement script runs

---

## Orchestrator (main Claude Code session)
- Routes tickets to the correct agent/subagent
- Commits after every confirmed working step
- Never manually modifies Blender — edits `.py` files only
- Keeps all scripts self-contained (run with Alt+P, no setup)

---

## Golden rules
1. **C10 = construction only** — no movement, no keyframes, nothing moves
2. **C12–C15, T01–T04 = movement only** — no scene building
3. Object names are fixed: `Cube_Blue`, `Ball`, `Hinge_Blue_Red`, etc.
4. Hinge Z is always `1.0` (top of unit cube)
5. Ball starts in Blue, travels Blue → Red → Green → Yellow
6. Every script registers safely (unregister before register)
7. Commit after every confirmed working step
