# LorQB — C10 Scene Build Skill

## What this script does
`C_series/C10_scene_build.py` is the **base scene initializer** for LorQB.
Running it clears the Blender scene and rebuilds everything from scratch:
4 hollow cubes, 1 ball, 3 hinges, and 4 seat empties.

---

## Scene topology (permanent constraint — never change)

```
Yellow (top-left)  ——  Blue (top-right)
       |                      |
Green (bottom-left) —— Red (bottom-right)

Chain order (clockwise): Blue → Red → Green → Yellow
```

### Cube hole config (matches original PDF dark bars)
| Cube   | Holes                              |
|--------|------------------------------------|
| Blue   | top + LEFT side (faces Yellow)     |
| Yellow | top + RIGHT side (faces Blue)      |
| Red    | top only                           |
| Green  | top only                           |

### Hinge locations (world space, Z=1)
| Hinge name         | Location        |
|--------------------|-----------------|
| Hinge_Blue_Red     | (0.51, 0, 1)    |
| Hinge_Red_Green    | (0, -0.51, 1)   |
| Hinge_Green_Yellow | (-0.51, 0, 1)   |

### Cube pivot origins (set to their hinge)
| Cube   | Pivot set to hinge  |
|--------|---------------------|
| Blue   | Hinge_Blue_Red      |
| Red    | Hinge_Red_Green     |
| Green  | Hinge_Green_Yellow  |
| Yellow | Hinge_Green_Yellow  |

### Seat empties (ball landing positions)
| Seat name    | Location              |
|--------------|-----------------------|
| Seat_Blue    | (0.51, 0.51, 0.0)     |
| Seat_Red     | (0.51, -0.51, 0.0)    |
| Seat_Green   | (-0.51, -0.51, 0.0)   |
| Seat_Yellow  | (-0.51, 0.51, 0.0)    |

---

## Key parameters (safe to adjust)

| Variable        | Default | Controls                        |
|-----------------|---------|---------------------------------|
| cube size       | 1.0     | outer cube edge length          |
| inner cube size | 0.955   | thickness of walls              |
| cylinder radius | 0.3     | hole opening size               |
| cylinder depth  | 0.6     | hole punch depth                |
| ball_radius     | 0.25    | ball size                       |
| Alpha           | 0.35    | cube transparency               |

---

## Blender UI panel (registered by this script)
- Panel: **LorQB — C10** (N-panel, LorQB tab, VIEW_3D)
- Buttons:
  - **Reset to Base** → clears scene (`lorqb.reset_c10`)
  - **Build Scene (C10)** → full rebuild (`lorqb.build_c10`)

---

## How to run in Blender
1. Open `C_series/C10_scene_build.py` in Blender Text Editor
2. Press **Alt+P** (or click Run Script)
3. Scene is cleared and rebuilt immediately
4. Use the N-panel LorQB tab to reset/rebuild later

---

## Constraints / invariants (never violate)
- Cube bottom faces must sit ON the ground (Z offset: `location[2] + 0.5`)
- Ball starts inside **Blue** cube, at `cube_bottom + ball_radius * 0.99`
- Hinge Z is always 1.0 (top of unit cube)
- All object names are fixed: `Cube_Blue`, `Cube_Red`, `Cube_Green`,
  `Cube_Yellow`, `Ball`, `Hinge_*`, `Seat_*`
- Script is **self-contained** — no manual Blender UI steps needed

---

## Common agent tasks for C10

**Task: Adjust cube transparency**
- Find `bsdf.inputs["Alpha"].default_value` and `mat.diffuse_color`
- Change the `0.35` value (both must match)

**Task: Resize holes**
- Find `radius=0.3` in both `primitive_cylinder_add` calls
- Change consistently for all holes

**Task: Add a new hinge**
- Add `bpy.ops.object.empty_add(...)` with new name
- Add corresponding `origin_set` for the affected cube

**Task: Debug — scene not clearing**
- Check `clear_scene()` — it removes all `bpy.data.objects`
- If custom collections exist, they may need explicit removal

---

## Related scripts (execution order)
```
C10  →  C12  →  C13  →  C14  →  C15
(build)  (B→R)  (R→G)  (G→Y)  (Y→B)
```
C01 (`C01_lorQB_Master_Runner.py`) provides the panel to run C12–C15 in sequence.
