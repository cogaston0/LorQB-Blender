# LorQB — Lord of the Quantum Balls

**Blender Version:** 5.0.1

**Original Design:** Jose R. Velazquez © 2014

**Developer:** Carlos

**AI System:** Rukmini Trio (Claude + ChatGPT + NotebookLM)

## File Structure

```
LorQB-Blender/
├── C10_scene_build.py          # Scene construction — run once to build the rig
├── C12_blue_to_red.py          # Sequence C12: ball transfer Blue → Red
├── C13_red_to_green.py         # Sequence C13: ball transfer Red → Green
├── C14_green_to_yellow.py      # Sequence C14: ball transfer Green → Yellow
├── C15_yellow_to_blue.py       # Sequence C15: hinge block Yellow → Blue (WIP)
├── lorqb_master_runner.py      # Master panel — registers all Cx operators at once
├── lorqb_video_game.pdf        # Original game design document
└── README.md
```

## Cube Chain Topology

```
Yellow (top-left) — Green (bottom-left) — Red (bottom-right) — Blue (top-right)
```

Hinges (created by C10):

| Hinge name          | Location       | Connects        |
|---------------------|----------------|-----------------|
| Hinge_Blue_Red      | ( 0.51,  0, 1) | Blue ↔ Red      |
| Hinge_Red_Green     | ( 0, -0.51, 1) | Red ↔ Green     |
| Hinge_Green_Yellow  | (-0.51,  0, 1) | Green ↔ Yellow  |

## Script Sequence

1. **C10** — Build the scene (cubes, ball, hinges). Run once per Blender session.
2. **C12** — Animate ball transfer: Blue → Red (frames 1–240).
3. **C13** — Animate ball transfer: Red → Green (frames 241–480).
4. **C14** — Animate ball transfer: Green → Yellow (frames 481–720).
5. **C15** — Animate hinge: Yellow → Blue (frames 1–240, WIP — ball transfer pending).

Use `lorqb_master_runner.py` to register all four Cx operator buttons in one panel
(N-panel → LorQB tab). Update the `SCRIPTS` path at the top of that file to match
your local scripts folder.

## Level 1 Status

- Goal: complete all sequences for Level 1 with modular, reorderable scripts.
- Current focus: C15 (Yellow → Blue) — hinge rotation confirmed, ball transfer pending.

## Key Design Notes

- Ball starts inside the active cube at the beginning of each turn.
- Each Cx script calls `reset_scene_to_canonical()` (or an equivalent reset) first,
  so any script can be run independently without depending on a prior run.
- Future: shuffle can select any cube order; scripts must support any permutation.

## Key Rules

- Script-only operations (no manual Blender UI).
- Commit after every confirmed working step.
