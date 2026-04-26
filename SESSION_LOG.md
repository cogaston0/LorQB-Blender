# LorQB Session Log — C-Series Completion
**Branch:** refactor/seats-uniformity  
**Commit:** c58ae37  
**Date:** 2026-04-26  

---

## What Was Completed

### C-Series Forward (C12–C15)
All four forward transfers working: Blue→Red, Red→Green, Green→Yellow, Yellow→Blue.

### C-Series REV (C12_REV–C15_REV)
All four reverse transfers working: Red→Blue, Green→Red, Yellow→Green, Blue→Yellow.

### Toggle UI (C01_lorQB_Master_Runner.py)
Master runner with toggle buttons for all C-series forward and REV scripts operational.

---

## Key Mechanical Decisions Made This Session

### 1. Seats at Geometric Center (Z=0.5), Not Z=0.07
- C10_scene_build was placing seats at Z=0.07 (floor of cube).
- Correct position: geometric center of each cube face = Z=0.5.
- All REV scripts use `CANON_SEATS` dict with Z=0.5 world positions.

### 2. Seat Local Offset Formula
Cube origins are at their respective **hinge positions**, not at cube mesh centers.
The local offset from hinge-origin to mesh center must be computed as:
```
local = mesh_center_world - hinge_origin_world
```
Example — Red: hinge=(0, -0.51, 1), mesh_center=(0.51, -0.51, 0.5) → local=(0.51, 0, -0.5)

Using `(0, 0, 0.25)` naively placed seats outside the cube (at hinge + 0.25 Z). **Never use naive local offsets.**

### 3. Hinge Topology Must Never Be Broken
Passive carry chain must respect the hinge hierarchy:
```
Hinge_Blue_Red → Cube_Red → Hinge_Red_Green → Cube_Green → Hinge_Green_Yellow → Cube_Yellow
```
Green must always be parented to `Hinge_Red_Green`, never directly to `Cube_Red`.
Violation causes cubes to detach from pivot positions mid-animation.

### 4. Seat Capture Convention
- `Seat_[Source]_Start`: captured at runtime from `ball.matrix_world` — never hardcoded.
- `Seat_[Dest]_World`: safe to hardcode (ball has not yet been there at frame 1).
- Hardcoding the source seat causes instant snap-jump when constraint activates.

### 5. FCurve API (Blender 5.0.1)
`action.fcurves` does not exist in 5.0.1. Use:
```python
action.layers[0].strips[0].channelbag_for_slot(action.slots[0]).fcurves
```
All constraint influence FCurves must use `CONSTANT` interpolation.

### 6. COPY_TRANSFORMS Only (Never CHILD_OF)
`CHILD_OF` constraint causes ball to land at wrong position.
All ball latching uses `COPY_TRANSFORMS` targeting seat empties.

---

## Bugs Fixed This Session
- Ball outside cube: wrong local seat offset (hinge origin ≠ mesh center)
- Green detaching: parented directly to Red instead of via Hinge_Red_Green
- Stale Blender buffer: required Text → Reload after disk edits via Claude Code CLI

---

## Next: T-Series REV
Branch `refactor/t-series-rev` will be created from this commit.
T-series REV files: T01_REV, T02_REV, T03_REV, T04_REV (diagonal two-hinge transfers).
ROT_SIGN values are always TODO — verified empirically, never assumed.
