# ============================================================================
# T03_red_to_yellow.py  (Blender 5.1.0)
# T3 — Red → Yellow  (yellow-first hinge sequence)
#
# CRITICAL RULE: Yellow initiates first. Red-delivery is TWO sequential motions:
#   Stage 2a — Hinge_Blue_Red rotates 90° (Y): Red swings toward Green
#   Stage 2b — Hinge_Red_Green rotates 90° (Y): whole system swings until Red is above Yellow
# Transfer does NOT happen during Stage 2b. It happens at frame 161 (latch switch) AFTER
# the 90° swing has placed Red over Yellow. Blue follows Red passively throughout.
#
# Scene layout:
#   Red   = bottom-right, one hole on top only
#   Yellow= top-left, two holes (top + right side)
#   Hinge_Blue_Red     connects Blue (top-right) to Red (bottom-right)
#   Hinge_Red_Green    connects Red/Blue assembly to Green (bottom-left)
#   Hinge_Green_Yellow connects Green (bottom-left) to Yellow (top-left)
#
# Ball path:
#   Frame   1:      Ball at Red interior  (Seat_Red_Start = ball world pos)
#   Frame   1– 80: Stage 1  — HGY rotates 180° (Yellow initiates ALONE)
#   Frame  81–120: Stage 2a — HBR rotates 90°  (Red swings toward Green)
#   Frame 121–160: Stage 2b — HRG rotates 90°  (system swings until Red is above Yellow)
#   Frame 161:     Transfer — Latch_Red_Start → 0, Latch_Yellow_Side → 1
#   Frame 162–200: Stage 4  — HRG returns 0°, HBR returns 0°
#   Frame 201–240: Stage 5  — HGY returns 0°
#
# Hierarchy:
#   Cube_Yellow        -> Hinge_Green_Yellow (Stage 1 / Stage 5)
#   Hinge_Green_Yellow -> Cube_Green
#   Cube_Green         -> Hinge_Red_Green    (Stage 2b / Stage 4)
#   Hinge_Blue_Red     -> Hinge_Red_Green    (Stage 2b / Stage 4)
#   Cube_Red           -> Hinge_Blue_Red     (Stage 2a / Stage 4)
#   Cube_Blue          -> Cube_Red           (passive — follows Red)
# ============================================================================

import bpy
import math
import mathutils

###############################################################################
# SECTION 1: Constants
###############################################################################

F_START    = 1
F_S1_END   = 80    # HGY reaches HGY_DEGREES   — Yellow initiates (Stage 1 done)
F_S2A_END  = 120   # HBR reaches HBR_DEGREES   — Red at Yellow (Stage 2a done)
F_S2_END   = 160   # HRG reaches HRG_DEGREES   — whole system rotated (Stage 2b done)
F_SWAP     = 161   # Ball transfers: Red is on top of Blue — Latch_Red_Start off, Latch_Yellow_Side on
F_RET1_END = 200   # HRG returns to 0°          (Stage 4 complete)
F_RET2_END = 240   # HGY returns to 0°          (Stage 5 complete)
F_END      = 240

HGY_AXIS      = 0       # Hinge_Green_Yellow axis used in T2 baseline
HGY_SIGN      = +1.0    # Keep consistent with T2 direction convention
HGY_DEGREES   = 180.0   # Yellow full flip envelope

HBR_AXIS      = 1       # Y-axis — Red swings toward Green
HBR_SIGN      = +1.0    # Positive Y — Red swings toward Yellow
HBR_DEGREES   = 90.0    # Stage 2a: Red rotates toward Green

HRG_AXIS      = 1       # Y-axis — whole system swings to drop ball into Yellow
HRG_SIGN      = -1.0    # Negative Y — system rotates for drop
HRG_DEGREES   = 90.0    # Stage 2b: system rotation

# Yellow side-hole center (parented to Yellow).
# TODO: verify exact world coordinate in Blender before running.
SEAT_YELLOW_SIDE_WORLD = mathutils.Vector((-0.51, 0.51, 0.25))  # Z = ball radius above Yellow's interior floor

# Seat_Red_Start is NEVER hardcoded — captured from ball.matrix_world at runtime.
# This constant is only used to place the ball before capture.
BALL_RED_INTERIOR = mathutils.Vector((0.51, -0.51, 0.25))

###############################################################################
# SECTION 2: Full Scene Reset
###############################################################################

def reset_scene_to_canonical():
    if bpy.app.driver_namespace.get("lorqb_run_all", False):
        print("=== T3 Reset skipped (Run ALL mode) ===")
        return

    # Clear animation data from all scene objects touched by T3
    for name in [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Green_Yellow", "Hinge_Red_Green",
    ]:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    # Clear ball constraints
    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    # Zero all hinge rotations
    for name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        h = bpy.data.objects.get(name)
        if h:
            h.rotation_mode = 'XYZ'
            h.rotation_euler = (0.0, 0.0, 0.0)

    # Unparent all cubes and hinges — then restore canonical positions/rotations
    for name in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
                 "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.parent = None

    bpy.context.view_layer.update()

    # Cube origins were moved to hinge positions by C10 — restore exactly
    canonical = {
        "Cube_Blue":            (0.51,  0.0,  1.0),  # pivot at Hinge_Blue_Red
        "Cube_Red":             (0.0,  -0.51, 1.0),  # pivot at Hinge_Red_Green
        "Cube_Green":           (-0.51, 0.0,  1.0),  # pivot at Hinge_Green_Yellow
        "Cube_Yellow":          (-0.51, 0.0,  1.0),  # pivot at Hinge_Green_Yellow
        "Hinge_Blue_Red":       (0.51,  0.0,  1.0),
        "Hinge_Red_Green":      (0.0,  -0.51, 1.0),
        "Hinge_Green_Yellow":   (-0.51, 0.0,  1.0),
    }
    for name, loc in canonical.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location      = loc
            obj.rotation_mode = 'XYZ'
            obj.rotation_euler = (0.0, 0.0, 0.0)

    # Delete all seat empties
    for name in ["Seat_Red_Start", "Seat_Yellow_Side",
                 "Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.context.view_layer.update()
    print("=== Scene reset to canonical state ===")

###############################################################################
# SECTION 3: Helpers
###############################################################################

def set_last_keyframe_interpolation(obj, data_path, frame, interp='LINEAR'):
    """Set interpolation on the keyframe nearest to `frame` on matching fcurves."""
    if not obj.animation_data or not obj.animation_data.action:
        return
    try:
        fcurves = obj.animation_data.action.layers[0].strips[0].channelbags[0].fcurves
    except Exception:
        return
    for fc in fcurves:
        if data_path in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp


def key_rot(obj, axis, sign, frame, degrees, interp='LINEAR'):
    """Insert a rotation keyframe on `obj` at `frame` and force interpolation."""
    bpy.context.scene.frame_set(frame)
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler[axis] = sign * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=axis, frame=frame)
    set_last_keyframe_interpolation(obj, "rotation_euler", frame, interp)


def key_influence(obj, constraint_name, frame, value):
    """Insert a CONSTANT-interpolated influence keyframe on a named constraint."""
    bpy.context.scene.frame_set(frame)
    con = obj.constraints.get(constraint_name)
    if not con:
        print(f"WARNING: Constraint '{constraint_name}' not found on {obj.name}")
        return
    con.influence = value
    data_path = f'constraints["{constraint_name}"].influence'
    obj.keyframe_insert(data_path=data_path, frame=frame)
    set_last_keyframe_interpolation(obj, data_path, frame, 'CONSTANT')


def parent_preserve_world(child, new_parent):
    """Re-parent `child` under `new_parent` without moving it in world space."""
    mw = child.matrix_world.copy()
    child.parent = new_parent
    bpy.context.view_layer.update()  # flush world matrices before capturing inverse
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw
    bpy.context.view_layer.update()  # commit the restored world position


def make_seat(name, parent_obj, world_pos):
    """Create a SPHERE empty parented to `parent_obj` at `world_pos`."""
    seat = bpy.data.objects.new(name, None)
    seat.empty_display_type = 'SPHERE'
    seat.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat)
    seat.parent = parent_obj
    seat.location = parent_obj.matrix_world.inverted() @ world_pos
    return seat

###############################################################################
# SECTION 4: Stage functions (one per button)
###############################################################################

# Module-level cache so Button 2 & 3 can find the objects set up by Button 1.
_t3_objects = {}


def _gather():
    """Return object dict or None on error."""
    names = {
        "blue":     "Cube_Blue",
        "red":      "Cube_Red",
        "green":    "Cube_Green",
        "yellow":   "Cube_Yellow",
        "ball":     "Ball",
        "hinge_br": "Hinge_Blue_Red",
        "hinge_rg": "Hinge_Red_Green",
        "hinge_gy": "Hinge_Green_Yellow",
    }
    objs = {k: bpy.data.objects.get(v) for k, v in names.items()}
    missing = [v for k, v in names.items() if objs[k] is None]
    if missing:
        print("ERROR: Missing objects:", missing)
        return None
    return objs


def stage1_yellow():
    """Button 1 — Reset scene, build hierarchy, key Yellow 0°→180° (HGY)."""
    print("=== T3 Button 1: Setup + Yellow 0°→180° ===")
    reset_scene_to_canonical()

    objs = _gather()
    if objs is None:
        return False
    _t3_objects.update(objs)

    blue, red, green = objs["blue"], objs["red"], objs["green"]
    yellow, ball     = objs["yellow"], objs["ball"]
    hinge_br         = objs["hinge_br"]
    hinge_rg         = objs["hinge_rg"]
    hinge_gy         = objs["hinge_gy"]

    # ── Zero hinges ────────────────────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    for h in (hinge_gy, hinge_rg, hinge_br):
        h.rotation_mode  = 'XYZ'
        h.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # ── Hierarchy — explicit local positions + identity parent inverse ──────
    # Stale matrix_parent_inverse from previous runs causes objects to jump.
    # Fix: reset it to Identity on every re-parent so world = parent + local.
    # HRG is root (world anchor at (0, -0.51, 1)).

    I4 = mathutils.Matrix.Identity(4)

    def attach(child, parent, local_xyz):
        child.parent               = parent
        child.matrix_parent_inverse = I4.copy()
        child.location             = local_xyz
        child.rotation_euler       = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

    # Branch 1: Green → HGY → Yellow
    attach(green,    hinge_rg, (-0.51,  0.51, 0.0))  # (-0.51,0,1)-(0,-0.51,1)
    attach(hinge_gy, green,    ( 0.0,   0.0,  0.0))  # same world pos as Green pivot
    attach(yellow,   hinge_gy, ( 0.0,   0.0,  0.0))  # same world pos as HGY

    # Branch 2: HBR → Red → Blue
    attach(hinge_br, hinge_rg, ( 0.51,  0.51, 0.0))  # (0.51,0,1)-(0,-0.51,1)
    attach(red,      hinge_br, (-0.51, -0.51, 0.0))  # (0,-0.51,1)-(0.51,0,1)
    attach(blue,     red,      ( 0.51,  0.51, 0.0))  # (0.51,0,1)-(0,-0.51,1)

    print("Hierarchy: HRG(root) → [Green→HGY→Yellow] + [HBR→Red→Blue]")

    # ── Remove rigid body ─────────────────────────────────────────────────
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    # ── Place ball inside Red ─────────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    ball.location = BALL_RED_INTERIOR.copy()
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()

    # ── Seat_Red_Start ────────────────────────────────────────────────────
    ball_world     = ball.matrix_world.translation.copy()
    seat_red_start = bpy.data.objects.new("Seat_Red_Start", None)
    seat_red_start.empty_display_type = 'SPHERE'
    seat_red_start.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_red_start)
    seat_red_start.parent   = red
    seat_red_start.location = red.matrix_world.inverted() @ ball_world
    bpy.context.view_layer.update()

    # ── Seat_Yellow_Side ──────────────────────────────────────────────────
    seat_yellow_side = make_seat("Seat_Yellow_Side", yellow, SEAT_YELLOW_SIDE_WORLD)
    bpy.context.view_layer.update()

    # ── Constraints ───────────────────────────────────────────────────────
    latch_red          = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name     = "Latch_Red_Start"
    latch_red.target   = seat_red_start
    latch_yellow       = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_yellow.name  = "Latch_Yellow_Side"
    latch_yellow.target = seat_yellow_side

    # ── HGY keyframes: 0°→180° (Stage 1), hold, return ───────────────────
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_START,    0)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_S1_END,   HGY_DEGREES)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_S2_END,   HGY_DEGREES)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_SWAP,     HGY_DEGREES)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_RET1_END, HGY_DEGREES)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_RET2_END, 0)
    print("HGY keyed: 0°→180° frames 1–80, hold 80–200, return 200–240.")

    # ── Ball influence initial keys ────────────────────────────────────────
    key_influence(ball, "Latch_Red_Start",   F_START, 1.0)
    key_influence(ball, "Latch_Yellow_Side", F_START, 0.0)

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)
    print("=== Stage 1 done. Press Play frames 1–80 to preview. ===")
    return True


def stage2a_red():
    """Button 2 — Key Red rotating toward Yellow (HBR Stage 2a, frames 81–120)."""
    print("=== T3 Button 2: Red rotates toward Yellow (HBR) ===")

    hinge_br = bpy.data.objects.get("Hinge_Blue_Red")
    if hinge_br is None:
        print("ERROR: Hinge_Blue_Red not found — run Button 1 first.")
        return False

    # Hold during Stage 1, rotate Stage 2a, hold through drop, return Stage 4
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_START,    0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S1_END,   0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S2A_END,  HBR_DEGREES)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_SWAP,     HBR_DEGREES)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET1_END, 0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET2_END, 0)
    print(f"HBR keyed: 0°→{HBR_DEGREES}° frames 81–120, return 162–200.")
    print("=== Stage 2a done. Press Play frames 81–120 to preview. ===")
    return True


def stage2b_drop():
    """Button 3 — Key system rotation + ball drop (HRG Stage 2b, frames 121–160)."""
    print("=== T3 Button 3: System rotation + Ball drop (HRG) ===")

    hinge_rg = bpy.data.objects.get("Hinge_Red_Green")
    ball     = bpy.data.objects.get("Ball")
    if hinge_rg is None or ball is None:
        print("ERROR: Hinge_Red_Green or Ball not found — run Button 1 first.")
        return False

    # Hold during Stages 1+2a, rotate Stage 2b, hold, return Stage 4
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_START,    0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2A_END,  0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2_END,   HRG_DEGREES)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_SWAP,     HRG_DEGREES)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET1_END, 0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET2_END, 0)
    print(f"HRG keyed: 0°→{HRG_DEGREES}° frames 121–160, return 162–200.")

    # Ball latch switch at frame 161
    key_influence(ball, "Latch_Red_Start",   F_S2_END, 1.0)
    key_influence(ball, "Latch_Red_Start",   F_SWAP,   0.0)
    key_influence(ball, "Latch_Red_Start",   F_END,    0.0)
    key_influence(ball, "Latch_Yellow_Side", F_S2_END, 0.0)
    key_influence(ball, "Latch_Yellow_Side", F_SWAP,   1.0)
    key_influence(ball, "Latch_Yellow_Side", F_END,    1.0)
    print("Ball latch: Red OFF / Yellow ON at frame 161.")
    print("=== Stage 2b done. Press Play frames 1–240 for full sequence. ===")
    return True


def run_animation():
    """Run all three stages at once (legacy / scripted entry-point)."""
    return stage1_yellow() and stage2a_red() and stage2b_drop()


###############################################################################
# SECTION 5: Entry Point
###############################################################################

if __name__ == "__main__":
    # Unregister any stale classes from previous script versions
    for name in ["LORQB_OT_t3_stage1", "LORQB_OT_t3_stage2a", "LORQB_OT_t3_stage2b",
                 "LORQB_PT_t3_panel", "LORQB_OT_run_t3"]:
        cls = getattr(bpy.types, name, None)
        if cls:
            try:
                bpy.utils.unregister_class(cls)
                print(f"Unregistered stale class: {name}")
            except Exception:
                pass

    ok = run_animation()
    if ok:
        print("T3 executed immediately. UI button also available in 3D View > N-panel > LorQB.")
    else:
        print("T3 did not execute. Check missing object errors in console output.")
