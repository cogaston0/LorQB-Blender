# ============================================================================
# T03_red_to_yellow.py  (Blender 5.0.1)
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
HBR_SIGN      = +1.0    # TODO: verify direction in Blender
HBR_DEGREES   = 90.0    # Stage 2a: Red rotates toward Green

HRG_AXIS      = 1       # Y-axis — whole system swings to drop ball into Yellow
HRG_SIGN      = +1.0    # TODO: verify direction in Blender
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

    # Unparent all cubes — restore them to world-space canonical positions
    for name in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj and obj.parent is not None:
            mw = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = mw

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
# SECTION 4: Main T3 Animation Logic
###############################################################################

def run_animation():
    print("=== T3 Start: Red → Yellow ===")

    reset_scene_to_canonical()

    # ── Gather objects ─────────────────────────────────────────────────────
    blue     = bpy.data.objects.get("Cube_Blue")
    red      = bpy.data.objects.get("Cube_Red")
    green    = bpy.data.objects.get("Cube_Green")
    yellow   = bpy.data.objects.get("Cube_Yellow")
    ball     = bpy.data.objects.get("Ball")
    hinge_br = bpy.data.objects.get("Hinge_Blue_Red")
    hinge_rg = bpy.data.objects.get("Hinge_Red_Green")
    hinge_gy = bpy.data.objects.get("Hinge_Green_Yellow")

    missing = [n for n, o in [
        ("Cube_Blue",          blue),
        ("Cube_Red",           red),
        ("Cube_Green",         green),
        ("Cube_Yellow",        yellow),
        ("Ball",               ball),
        ("Hinge_Blue_Red",     hinge_br),
        ("Hinge_Red_Green",    hinge_rg),
        ("Hinge_Green_Yellow", hinge_gy),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    # ── Canonical starting state ───────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    hinge_gy.rotation_mode = 'XYZ'
    hinge_gy.rotation_euler = (0.0, 0.0, 0.0)
    hinge_rg.rotation_mode = 'XYZ'
    hinge_rg.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # ── Hierarchy ──────────────────────────────────────────────────────────
    # Red is a direct child of HRG (Red-Green boundary) — no detachment possible.
    # When HRG rotates, Red+Blue swing around the boundary point with Green.
    parent_preserve_world(yellow,   hinge_gy)
    parent_preserve_world(hinge_gy, green)
    parent_preserve_world(hinge_rg, green)   # HRG child of Green — Stage 2b pivot
    parent_preserve_world(hinge_br, hinge_rg) # HBR child of HRG — Stage 2a pivot
    parent_preserve_world(red,      hinge_br) # Red pivots at Blue-Red boundary
    parent_preserve_world(blue,     red)      # Blue follows Red passively
    bpy.context.view_layer.update()
    print("Hierarchy: Yellow→HGY→Green→HRG→HBR→Red→Blue.")

    # ── Remove rigid body from ball ────────────────────────────────────────
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    # ── Place ball at Red interior center ─────────────────────────────────
    # Must happen before Seat_Red_Start capture.
    bpy.context.scene.frame_set(F_START)
    ball.location = BALL_RED_INTERIOR.copy()
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()
    print(f"Ball placed at Red interior {BALL_RED_INTERIOR[:]}.")

    # ── Seat_Red_Start ─────────────────────────────────────────────────────
    # Captured from ball.matrix_world.translation — NEVER hardcoded.
    # Parented to Red so it travels with Red through Stages 1 and 2.
    ball_world     = ball.matrix_world.translation.copy()
    seat_red_start = bpy.data.objects.new("Seat_Red_Start", None)
    seat_red_start.empty_display_type = 'SPHERE'
    seat_red_start.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_red_start)
    seat_red_start.parent   = red
    seat_red_start.location = red.matrix_world.inverted() @ ball_world
    bpy.context.view_layer.update()
    print(f"Seat_Red_Start captured at ball world pos {ball_world} (no jump).")

    # ── Seat_Yellow_Side ───────────────────────────────────────────────────
    # Seat at Yellow's side-hole center, parented to Yellow.
    # Computed in Yellow local space at canonical orientation so the seat
    # follows Yellow through Stage 1/2 motion and Stage 4/5 return.
    seat_yellow_side = make_seat("Seat_Yellow_Side", yellow, SEAT_YELLOW_SIDE_WORLD)
    bpy.context.view_layer.update()
    print(f"Seat_Yellow_Side at world ref {SEAT_YELLOW_SIDE_WORLD[:]}.")

    # ── COPY_TRANSFORMS constraints ────────────────────────────────────────
    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name   = "Latch_Red_Start"
    latch_red.target = seat_red_start

    latch_yellow = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_yellow.name   = "Latch_Yellow_Side"
    latch_yellow.target = seat_yellow_side

    print("Latch_Red_Start and Latch_Yellow_Side created.")

    # ── Hinge_Green_Yellow keyframes (Yellow moves first) ─────────────────
    #
    # Stage 1  (  1– 80): 0° → HGY_DEGREES
    # Hold     ( 80–200): HGY_DEGREES
    # Stage 5  (201–240): HGY_DEGREES → 0°

    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_START,    0)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_S1_END,   HGY_DEGREES)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_S2_END,   HGY_DEGREES)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_SWAP,     HGY_DEGREES)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_RET1_END, HGY_DEGREES)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_RET2_END, 0)
    print("Hinge_Green_Yellow keyed: Stage 1 (1–80), hold (80–200), Stage 5 (201–240).")

    # ── Hinge_Blue_Red keyframes (Stage 2a — Red toward Green) ───────────
    #
    # Hold     (  1– 80): 0°              — waits for Yellow Stage 1
    # Stage 2a ( 81–120): 0° → HBR_DEGREES — Red swings toward Green
    # Hold     (120–161): HBR_DEGREES     — holds during Stage 2b
    # Stage 4  (162–200): HBR_DEGREES → 0°
    # Hold     (200–240): 0°

    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_START,    0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S1_END,   0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S2A_END,  HBR_DEGREES)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_SWAP,     HBR_DEGREES)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET1_END, 0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET2_END, 0)
    print("Hinge_Blue_Red keyed: Stage 2a (81–120) Red toward Green, Stage 4 return (162–200).")

    # ── Hinge_Red_Green keyframes (Stage 2b — system drops ball into Yellow)
    #
    # Hold     (  1–120): 0°              — waits for Stage 1 + Stage 2a
    # Stage 2b (121–160): 0° → HRG_DEGREES — system swings, ball drops into Yellow
    # Hold     (160–161): HRG_DEGREES
    # Stage 4  (162–200): HRG_DEGREES → 0°
    # Hold     (200–240): 0°

    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_START,    0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2A_END,  0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2_END,   HRG_DEGREES)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_SWAP,     HRG_DEGREES)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET1_END, 0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET2_END, 0)
    print("Hinge_Red_Green keyed: Stage 2b (121–160) positions Red above Yellow, Stage 4 return (162–200).")


    # ── Ball constraint influences ─────────────────────────────────────────
    #
    # Latch_Red_Start:   1.0 frames 1–160  →  0.0 from frame 161 onward
    # Latch_Yellow_Side: 0.0 frames 1–160  →  1.0 from frame 161 onward
    #
    # All CONSTANT — hard switch at frame 161 (Red is on top of Blue).

    key_influence(ball, "Latch_Red_Start",   F_START,  1.0)
    key_influence(ball, "Latch_Red_Start",   F_S2_END, 1.0)
    key_influence(ball, "Latch_Red_Start",   F_SWAP,   0.0)
    key_influence(ball, "Latch_Red_Start",   F_END,    0.0)

    key_influence(ball, "Latch_Yellow_Side", F_START,  0.0)
    key_influence(ball, "Latch_Yellow_Side", F_S2_END, 0.0)
    key_influence(ball, "Latch_Yellow_Side", F_SWAP,   1.0)
    key_influence(ball, "Latch_Yellow_Side", F_END,    1.0)

    print("Influences keyed — Latch_Red_Start off / Latch_Yellow_Side on at frame 161 (Red on top of Blue).")

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== T3 Complete: Red → Yellow ===")
    return True

###############################################################################
# SECTION 5: N-Panel UI
###############################################################################

class LORQB_OT_run_t3(bpy.types.Operator):
    bl_idname      = "lorqb.run_t3"
    bl_label       = "Run T3: Red → Yellow"
    bl_description = "Arm T3 animation: Red transfers ball to Yellow via side hole"

    def execute(self, context):
        result = run_animation()
        if result:
            self.report({'INFO'}, "T3 armed — press Play to run")
        else:
            self.report({'ERROR'}, "T3 failed — check console for missing objects")
        return {'FINISHED'}


class LORQB_PT_t3_panel(bpy.types.Panel):
    bl_label       = "LorQB — T3"
    bl_idname      = "LORQB_PT_t3_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout
        layout.label(text="T3: Red → Yellow")
        layout.operator("lorqb.run_t3", icon='PLAY')


_classes = [LORQB_OT_run_t3, LORQB_PT_t3_panel]


def register():
    # Remove stale class registrations from previous script reloads.
    for cls in _classes:
        old_cls = getattr(bpy.types, cls.__name__, None)
        if old_cls is not None:
            try:
                bpy.utils.unregister_class(old_cls)
            except Exception:
                pass

    for cls in _classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"WARNING: Failed to register {cls.__name__}: {e}")


def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

###############################################################################
# SECTION 6: Entry Point
###############################################################################

if __name__ == "__main__":
    register()
    ok = run_animation()
    if ok:
        print("T3 executed immediately. UI button also available in 3D View > N-panel > LorQB.")
    else:
        print("T3 did not execute. Check missing object errors in console output.")
