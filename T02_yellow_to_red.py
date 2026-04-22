# ============================================================================
# T02_yellow_to_red.py  (Blender 5.0.1)
# T2 — Yellow → Red (diagonal, 2-stage per LORQB_T_SERIES_MOVE_SPEC.md)
#
# Motion:
#   Stage 1 (F_START → F_MID):  HGY +180° on X  — Yellow flips
#   Stage 2 (F_MID   → F_HOLD): HRG  -90° on Y  — Green+Yellow over Red
#   F_HOLD → F_SWAP:  ball transfers Yellow → Red via latch switch
#   F_SWAP → F_RET → F_END: motion reverses (HRG back, then HGY back)
# Hierarchy: HRG → Green → HGY → Yellow  (Red stays fixed, no re-parenting)
# ============================================================================

import bpy
import math
import mathutils

###############################################################################
# SECTION 1: Constants
###############################################################################

F_START        = 1
F_MID          = 60    # HGY reaches +180° on X — Yellow flipped
F_HOLD         = 120   # HRG reaches -90°  on Y — Yellow above Red, aligned
F_SWAP         = 121   # Ball transfers Yellow → Red
F_RET          = 180   # HRG returns to 0°
F_END          = 240   # HGY returns to 0°

# Axis + sign per LORQB_T_SERIES_MOVE_SPEC.md (T02 row, final)
ROT_SIGN_HGY   = +1.0  # HGY X-axis, +180°
ROT_SIGN_HRG   = +1.0  # HRG Y-axis, +90°
AXIS_HGY       = 0     # X
AXIS_HRG       = 1     # Y

# Red bottom interior center (destination seat target)
SEAT_RED_WORLD = mathutils.Vector((0.51, -0.51, 0.25))

# ---- Four-Seat Contract (T-series start geometry; ball-interior Z=0.25) ----
CANON_SEATS = {
    "Seat_Blue":   (mathutils.Vector(( 0.51,  0.51, 0.25)), "Cube_Blue"),
    "Seat_Red":    (mathutils.Vector(( 0.51, -0.51, 0.25)), "Cube_Red"),
    "Seat_Green":  (mathutils.Vector((-0.51, -0.51, 0.25)), "Cube_Green"),
    "Seat_Yellow": (mathutils.Vector((-0.51,  0.51, 0.25)), "Cube_Yellow"),
}

def ensure_four_seats():
    for seat_name in CANON_SEATS:
        stale = bpy.data.objects.get(seat_name)
        if stale:
            bpy.data.objects.remove(stale, do_unlink=True)
    bpy.context.view_layer.update()
    for seat_name, (world_vec, cube_name) in CANON_SEATS.items():
        cube = bpy.data.objects.get(cube_name)
        if cube is None:
            continue
        seat = bpy.data.objects.new(seat_name, None)
        seat.empty_display_type = 'SPHERE'
        seat.empty_display_size = 0.08
        bpy.context.scene.collection.objects.link(seat)
        seat.parent   = cube
        seat.location = cube.matrix_world.inverted() @ world_vec
    bpy.context.view_layer.update()

def validate_four_seats(label):
    print(f"--- FOUR-SEAT REPORT [{label}] ---")
    ok = True
    for seat_name in ("Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"):
        seat = bpy.data.objects.get(seat_name)
        if seat is None:
            print(f"  {seat_name}: <missing>  FAIL")
            ok = False
            continue
        w = seat.matrix_world.translation
        print(f"  {seat_name}: ({w.x:+.4f},{w.y:+.4f},{w.z:+.4f})  OK")
    print(f"--- FOUR-SEAT [{label}] → {'PASS' if ok else 'FAIL'} ---")
    return ok

def hard_fail_missing_seats():
    missing = [n for n in CANON_SEATS if bpy.data.objects.get(n) is None]
    if missing:
        print("ABORT: missing canonical seats:", missing)
        return False
    return True

###############################################################################
# SECTION 2: Full Scene Reset
###############################################################################

def reset_scene_to_canonical():
    if bpy.app.driver_namespace.get("lorqb_run_all", False):
        print("=== T2 Reset skipped (Run ALL mode) ===")
        return

    all_names = [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
        "Seat_Yellow_Start",
        "Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow",
    ]
    for name in all_names:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    for seat_name in ["Seat_Yellow_Start",
                      "Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)
    bpy.context.view_layer.update()

    # Unparent all cubes + hinges, clear constraints.
    for name in ("Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
                 "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.parent = None
            obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
            for con in list(obj.constraints):
                obj.constraints.remove(con)
    bpy.context.view_layer.update()

    # Restore canonical world positions (C10 origin-aware placement).
    CANON_CUBES_T02 = {
        "Cube_Blue":   mathutils.Vector(( 0.51,  0.00, 1.0)),
        "Cube_Red":    mathutils.Vector(( 0.00, -0.51, 1.0)),
        "Cube_Green":  mathutils.Vector((-0.51,  0.00, 1.0)),
        "Cube_Yellow": mathutils.Vector((-0.51,  0.00, 1.0)),
    }
    CANON_HINGES_T02 = {
        "Hinge_Blue_Red":     mathutils.Vector(( 0.51,  0.00, 1.0)),
        "Hinge_Red_Green":    mathutils.Vector(( 0.00, -0.51, 1.0)),
        "Hinge_Green_Yellow": mathutils.Vector((-0.51,  0.00, 1.0)),
    }
    for name, loc in CANON_CUBES_T02.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location       = (loc.x, loc.y, loc.z)
            obj.rotation_mode  = 'XYZ'
            obj.rotation_euler = (0.0, 0.0, 0.0)
    for name, loc in CANON_HINGES_T02.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location       = (loc.x, loc.y, loc.z)
            obj.rotation_mode  = 'XYZ'
            obj.rotation_euler = (0.0, 0.0, 0.0)

    bpy.context.view_layer.update()
    print("=== T2 reset: full canonical restore (4 cubes + 3 hinges) ===")

###############################################################################
# SECTION 3: Helpers
###############################################################################

def set_last_keyframe_interpolation(obj, data_path, frame, interp='LINEAR'):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    try:
        fcurves = action.layers[0].strips[0].channelbags[0].fcurves
    except Exception:
        return
    for fc in fcurves:
        if fc.data_path == data_path or data_path in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp

def key_rot(obj, axis, sign, frame, degrees, interp='LINEAR'):
    bpy.context.scene.frame_set(frame)
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler[axis] = sign * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=axis, frame=frame)
    set_last_keyframe_interpolation(obj, "rotation_euler", frame, interp)

def key_influence(obj, constraint_name, frame, value):
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
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw

###############################################################################
# SECTION 4: Main T2 Animation Logic
###############################################################################

def run_animation():
    print("=== T2 Start: Yellow → Red ===")

    reset_scene_to_canonical()

    yellow = bpy.data.objects.get("Cube_Yellow")
    green  = bpy.data.objects.get("Cube_Green")
    red    = bpy.data.objects.get("Cube_Red")
    ball   = bpy.data.objects.get("Ball")
    hinge1 = bpy.data.objects.get("Hinge_Green_Yellow")
    hinge2 = bpy.data.objects.get("Hinge_Red_Green")

    missing = [n for n, o in [
        ("Cube_Yellow",        yellow),
        ("Cube_Green",         green),
        ("Cube_Red",           red),
        ("Ball",               ball),
        ("Hinge_Green_Yellow", hinge1),
        ("Hinge_Red_Green",    hinge2),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    bpy.context.scene.frame_set(F_START)
    hinge1.rotation_euler = (0, 0, 0)
    hinge2.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # ── Hierarchy ──────────────────────────────────────────────────────────
    # Full chain so HGY stays mechanically attached while HRG rotates:
    #   HRG → Green → HGY → Yellow
    # Red stays fixed (anchored by HBR which does not rotate).
    parent_preserve_world(green,  hinge2)   # Green rides HRG
    parent_preserve_world(hinge1, green)    # HGY rides Green
    parent_preserve_world(yellow, hinge1)   # Yellow rides HGY
    print("Hierarchy set: HRG→Green→HGY→Yellow  (Red fixed)")

    # ── Remove rigid body from ball ────────────────────────────────────────
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    bpy.context.view_layer.update()

    # ── Move ball to Yellow's bottom interior center ─────────────────────
    # Ball starts inside Blue by default (C10_scene_build). Reposition it
    # to Yellow before capturing Seat_Yellow_Start.
    ball.location = mathutils.Vector((-0.51, 0.51, 0.25))
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()
    print("Ball moved to Yellow bottom interior center (-0.51, 0.51, 0.25).")

    # ── Four-Seat Contract — build ALL 4 canonical seats ─────────────────────
    ensure_four_seats()
    if not validate_four_seats("after ensure_four_seats"):
        print("ABORT: four-seat validation failed at build time.")
        return False
    if not hard_fail_missing_seats():
        return False

    seat_yellow = bpy.data.objects.get("Seat_Yellow")
    seat_red    = bpy.data.objects.get("Seat_Red")

    # ── Constraints ────────────────────────────────────────────────────────
    latch_yellow = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_yellow.name   = "Latch_Yellow"
    latch_yellow.target = seat_yellow

    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name   = "Latch_Red"
    latch_red.target = seat_red
    print("Latch_Yellow and Latch_Red created.")

    # ── Hinge keyframes (two-stage diagonal per spec) ──────────────────────
    # Stage 1 (F_START → F_MID):  HGY 0° → +180° on X
    # Stage 2 (F_MID   → F_HOLD): HRG 0° → -90°  on Y
    # Hold    (F_HOLD  → F_SWAP): both held
    # Return 1(F_SWAP  → F_RET):  HRG -90° → 0°
    # Return 2(F_RET   → F_END):  HGY +180° → 0°
    key_rot(hinge1, AXIS_HGY, ROT_SIGN_HGY, F_START,   0)
    key_rot(hinge1, AXIS_HGY, ROT_SIGN_HGY, F_MID,   180)
    key_rot(hinge1, AXIS_HGY, ROT_SIGN_HGY, F_HOLD,  180)
    key_rot(hinge1, AXIS_HGY, ROT_SIGN_HGY, F_SWAP,  180)
    key_rot(hinge1, AXIS_HGY, ROT_SIGN_HGY, F_RET,   180)
    key_rot(hinge1, AXIS_HGY, ROT_SIGN_HGY, F_END,     0)

    key_rot(hinge2, AXIS_HRG, ROT_SIGN_HRG, F_START,   0)
    key_rot(hinge2, AXIS_HRG, ROT_SIGN_HRG, F_MID,     0)
    key_rot(hinge2, AXIS_HRG, ROT_SIGN_HRG, F_HOLD,   90)
    key_rot(hinge2, AXIS_HRG, ROT_SIGN_HRG, F_SWAP,   90)
    key_rot(hinge2, AXIS_HRG, ROT_SIGN_HRG, F_RET,     0)
    key_rot(hinge2, AXIS_HRG, ROT_SIGN_HRG, F_END,     0)

    print("HGY keyframes: 0→180→0 on X. HRG keyframes: 0→-90→0 on Y.")

    # ── Ball constraint influences ─────────────────────────────────────────
    #
    # Latch_Yellow_Start: ON  frames 1–160, OFF from 161 onward
    # Latch_Red:          OFF frames 1–160, ON  from 161 onward
    #
    # All use CONSTANT interpolation — switches are intentional, not jumps.

    # Latch_Yellow
    key_influence(ball, "Latch_Yellow", F_START, 1.0)
    key_influence(ball, "Latch_Yellow", F_HOLD,  1.0)
    key_influence(ball, "Latch_Yellow", F_SWAP,  0.0)
    key_influence(ball, "Latch_Yellow", F_END,   0.0)

    # Latch_Red
    key_influence(ball, "Latch_Red",    F_START, 0.0)
    key_influence(ball, "Latch_Red",    F_HOLD,  0.0)
    key_influence(ball, "Latch_Red",    F_SWAP,  1.0)
    key_influence(ball, "Latch_Red",    F_END,   1.0)

    print(f"Influences keyed — Yellow→Red at frame {F_SWAP}.")

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)
    validate_four_seats("T02 final")

    print("=== T2 Complete: Yellow → Red ===")
    return True

###############################################################################
# SECTION 5: N-Panel UI
###############################################################################

class LORQB_OT_reset_t2(bpy.types.Operator):
    bl_idname      = "lorqb.reset_t2"
    bl_label       = "Reset to Base"
    bl_description = "Reset all objects to canonical state"

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "T2 reset to base")
        return {'FINISHED'}


class LORQB_OT_run_t2(bpy.types.Operator):
    bl_idname      = "lorqb.run_t2"
    bl_label       = "Run T2: Yellow → Red"
    bl_description = "Arm T2 animation: Yellow transfers ball to Red (diagonal)"

    def execute(self, context):
        result = run_animation()
        if result:
            self.report({'INFO'}, "T2 armed — press Play to run")
        else:
            self.report({'ERROR'}, "T2 failed — check console for missing objects")
        return {'FINISHED'}


class LORQB_PT_t2_panel(bpy.types.Panel):
    bl_label       = "LorQB — T2"
    bl_idname      = "LORQB_PT_t2_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_t2", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.run_t2", text="Run T2: Yellow → Red", icon='PLAY')


_classes = [LORQB_OT_reset_t2, LORQB_OT_run_t2, LORQB_PT_t2_panel]

def setup_yellow_to_red():
    return run_animation()

def register():
    for cls in _classes:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

###############################################################################
# SECTION 6: Entry Point
###############################################################################

register()
