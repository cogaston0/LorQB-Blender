# LorQB — Agent & Subagent Roles

## Project identity
**LorQB (Lord of the Quantum Balls)** — Blender 3D animation project.
A ball travels through a chain of 4 hollow colored cubes (Blue, Red, Green, Yellow)
linked by hinges. Scripts drive all animation — no manual Blender UI steps.

AI development team: **Rukmini Trio** (Claude + ChatGPT + NotebookLM)
Lead developer: Carlos | Original design: Jose R. Velazquez (2014)
Repo: `cogaston0/lorqb-blender` | Branch: `claude/organize-lorqb-skills-3UOBD`

---

## Agent (orchestrator role — Claude Code main session)

The main Claude Code session acts as the **orchestrator agent**. It:
- Understands the full C/T series dependency chain
- Decides which subagent to spawn for a given task
- Commits and pushes changes to the correct branch
- Keeps scripts self-contained (no external dependencies)
- Never manually modifies Blender — only edits `.py` files

---

## Subagent roles

### `scene-geometry` subagent
**Handles:** cube shape, hole sizes, material colors, transparency
**Primary file:** `C_series/C10_scene_build.py`
**Spawn when:** changing cube dimensions, hole configs, ball radius, colors

### `animation-keyframe` subagent
**Handles:** keyframe insertion, rotation angles, frame timing
**Primary files:** `C_series/C12–C15`, `T_series/T01–T04`
**Spawn when:** adjusting rotation curves, swap frame positions, easing

### `hinge-pivot` subagent
**Handles:** hinge empty placement, cube origin/pivot reassignment
**Primary files:** `C10` (setup), `C12–C15` (used during animation)
**Spawn when:** adding new hinges, changing pivot points, fixing detachment bugs

### `ball-transfer` subagent
**Handles:** ball parent swap logic (cube → hinge → next cube), seat empties
**Primary files:** all animation scripts (C12–C15, T01–T04)
**Spawn when:** ball misses seat, wrong swap frame, parent chain breaks

### `panel-ui` subagent
**Handles:** Blender operator/panel registration, N-panel buttons
**Primary files:** `C01_lorQB_Master_Runner.py`, `C10` panel section
**Spawn when:** adding new buttons, fixing class conflicts, registration errors

---

## Artifact catalog

| Artifact                        | Type      | Series | Status  |
|---------------------------------|-----------|--------|---------|
| `C_series/C10_scene_build.py`   | Scene     | C      | Done    |
| `C_series/C12_blue_to_red.py`   | Animation | C      | Done    |
| `C_series/C13_red_to_green.py`  | Animation | C      | Done    |
| `C_series/C14_green_to_yellow.py` | Animation | C    | Done    |
| `C_series/C15_yellow_to_blue.py`  | Animation | C    | Done    |
| `C_series/C01_lorQB_Master_Runner.py` | Panel | C   | Done    |
| `T_series/T01_blue_to_green.py` | Animation | T      | Done    |
| `T_series/T02_yellow_to_red.py` | Animation | T      | Done    |
| `T_series/T03_red_to_yellow.py` | Animation | T      | Done    |
| `T_series/T04_green_to_blue.py` | Animation | T      | Done    |

---

## Skill index (slash commands)

| Skill                             | Covers   |
|-----------------------------------|----------|
| `/lorqb-c10-scene-build`          | C10      |
| `/lorqb-c12-blue-to-red`          | C12      |
| `/lorqb-c13-red-to-green`         | C13      |
| `/lorqb-c14-green-to-yellow`      | C14      |
| `/lorqb-c15-yellow-to-blue`       | C15      |
| `/lorqb-t01-blue-to-green`        | T01      |
| `/lorqb-t02-yellow-to-red`        | T02      |
| `/lorqb-t03-red-to-yellow`        | T03      |
| `/lorqb-t04-green-to-blue`        | T04      |
| `/lorqb-agents`                   | this file |

---

## Golden rules (apply to all scripts)
1. All scripts are **self-contained** — run with Alt+P, no setup needed
2. Object names are **fixed** (`Cube_Blue`, `Ball`, `Hinge_Blue_Red`, etc.)
3. Hinge Z is always **1.0** (top of unit cube)
4. Ball starts in **Blue**, travels Blue → Red → Green → Yellow
5. Every script must **register safely** (unregister before register)
6. Commit after every confirmed working step
