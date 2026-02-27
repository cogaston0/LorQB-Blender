# LorQB Script Architecture Comparison

Comparison of animation architecture across the three core sequence scripts.

---

## Comparison Table

| Feature | `lorqb_blue_to_red.py` | `lorqb_red_to_green_C13.py` | `lorqb_green_flip_cycle.py` |
|---|---|---|---|
| **COPY_TRANSFORMS** | ❌ Not used | ✅ Two constraints: `Latch_Red` (targets `Seat_Red`) and `Latch_Green` (targets `Seat_Green`) | ❌ Not used |
| **CHILD_OF constraint** | ❌ Not used | ❌ Not used | ❌ Not used |
| **Direct parenting (`.parent =`)** | ✅ `blue_cube → hinge` (f1), `ball → blue_cube` (f1), `ball → red_cube` (f121) | ✅ `blue → red` (setup), `red → hinge_rg` (setup), seat empties parented to their cube | ✅ `ball → green_cube` (f1), `ball → None` (f120), `ball → yellow_cube` (f120) |
| **`matrix_parent_inverse` applied** | ✅ On `blue_cube → hinge` to preserve world transform; intentionally omitted on `ball → cube` so ball rides inside | ✅ Via `parent_preserve_world()` helper on every structural reparent | ❌ Not applied |
| **Direct location keyframes** | ❌ Not used | ❌ Not used | ✅ `ball.location` manually calculated from `yellow_cube.location` and dimensions before re-parenting at f120 |
| **Constraint influence keyframes** | ❌ None | ✅ `Latch_Red` and `Latch_Green` influence toggled 1.0 ↔ 0.0 at transfer frame (f361) using `keyframe_insert` | ❌ None |
| **Seat / anchor empties** | ❌ None | ✅ `Seat_Red` and `Seat_Green` empties created programmatically inside each cube as constraint targets | ❌ None |
| **Ball transfer mechanism** | Direct `.parent` swap at f121 | COPY_TRANSFORMS influence flip at f361 (`Latch_Red 1→0`, `Latch_Green 0→1`) | Unparent to `None`, set `ball.location` manually, re-parent to `yellow_cube` at f120 |
| **Hinge rotation axis** | X-axis (`rotation_euler[0]`) | Y-axis (`rotation_euler[1]`, via `ROT_AXIS = 1`) | X-axis (`rotation_euler[0]`) |
| **Frame range** | f1 – f240 | f241 – f480 | f1 – f240 |
| **Helper functions** | None (inline logic only) | `parent_preserve_world()`, `key_rot_y()`, `key_influence()` | None (inline logic only) |
| **Object validation** | `bpy.data.objects.get()` + `all([...])` guard | Named-object loop with list comprehension; prints missing names | `bpy.data.objects.get()` + `all([...])` guard |
| **Animation data cleared before setup** | ✅ `ball`, `hinge`, `blue_cube` | ✅ `hinge_rg` only (constraints replace prior ball animation) | ✅ `ball`, `hinge_green_yellow` |

---

## Architecture Summary

### `lorqb_blue_to_red.py` — Direct Parenting Model
- **Simplest architecture.** No constraints are used at any point.
- Ball transfer is achieved by swapping `.parent` mid-sequence (f121).
- `matrix_parent_inverse` is applied selectively: on the cube-to-hinge link to
  keep the cube in place, but deliberately omitted on ball-to-cube so the ball
  rides inside the cube during the flip.
- All animation is expressed as rotation keyframes on the hinge; the ball
  inherits movement passively through the parent chain.

### `lorqb_red_to_green_C13.py` — Constraint-Driven Model
- **Most structured architecture.** Introduces seat empties, a reusable helper
  library, and constraint influence keyframing.
- Ball position is controlled entirely by COPY_TRANSFORMS constraints targeting
  `Seat_Red` / `Seat_Green` empties. No `.parent` swap is used for the ball.
- `parent_preserve_world()` centralises all structural reparenting with world-
  transform preservation.
- Transfer frame uses a 1-frame CONSTANT-interpolation influence flip
  (recommended: set manually in Graph Editor).
- Frame range is offset (f241–f480) to chain after C12.

### `lorqb_green_flip_cycle.py` — Unparent + Manual Location Model
- **Transitional architecture** between direct parenting and constraints.
- Uses direct parenting for the initial phase, then unparents the ball (`parent = None`)
  at f120, manually calculates the target world location from `yellow_cube.location`
  and its dimensions, sets `ball.location` directly, and re-parents.
- No `matrix_parent_inverse` handling, which can cause visual snapping if the
  cube has a non-identity world transform at transfer time.
- Does not use constraints or seat empties; the manual location calculation is a
  workaround for the lack of a constraint target.
