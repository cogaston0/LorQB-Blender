# ============================================================================
# lorqb_blue_to_red_C12.py  (Blender 5.0.1)
# C12 — Blue → Red
# Frames 1 – 240 | Transfer at frame 120 → 121
# Chain: Blue — Red — Green — Yellow
# Hinge: Hinge_Blue_Red (X-axis rotation, ROT_SIGN = +1.0)
# Ball rides Cube_Blue (Latch_Blue) → drops into Cube_Red (Latch_Red)
# Architecture: matches C13 reference standard
# ============================================================================

import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
################################################################################
F_START    = 1
F_MID      = 60
F_HOLD     = 120
F_SWAP     = 121
F_RET      = 180
F_END      = 240

ROT_AXIS   = 0
ROT_SIGN   = +1.0
BALL_RADIUS = 0.25

# ---- Four-Seat Contract (Z=0.5 cube center; LORQB_BALL_STATE_STANDARD.md §4) ----
CANON_SEATS = {
    "Seat_Blue":   (mathutils.Vector(( 0.51,  0.51, 0.5)), "Cube_Blue"),
    "Seat_Red":    (mathutils.Vector(( 0.51, -0.51, 0.5)), "Cube_Red"),
    "Seat_Green":  (mathutils.Vector((-0.51, -0.51, 0.5)), "Cube_Green"),
    "Seat_Yellow": (mathutils.Vector((-0.51,  0.51, 0.5)), "Cube_Yellow"),
}

SEAT_RED_WORLD = CANON_SEATS["Seat_Red"][0]

################################################################################
# SECTION 1B: Four-Seat Contract helpers (shared block — identical in all scripts)
################################################################################
def ensure_four_seats():
    """Create all four canonical seats at Z=0.5, parented to their cubes.
    Removes any stale seat first. No substitute names."""
    for seat_name, (world_vec, cube_name) in CANON_SEATS.items():
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
    """Report all four seats and their world translations. Returns True if all
    four present AND each Z is 0.5 within tolerance."""
    print(f"--- FOUR-SEAT REPORT [{label}] ---")
    ok = True
    for seat_name in ("Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"):
        seat = bpy.data.objects.get(seat_name)
        if seat is None:
            print(f"  {seat_name}: <missing>  FAIL")
            ok = False
            continue
        w = seat.matrix_world.translation
        z_ok = abs(w.z - 0.5) <= 1e-3
        tag = "OK" if z_ok else "FAIL(Z)"
        if not z_ok:
            ok = False
        print(f"  {seat_name}: ({w.x:+.4f},{w.y:+.4f},{w.z:+.4f}) Z=0.5 {tag}")
    print(f"--- FOUR-SEAT [{label}] → {'PASS' if ok else 'FAIL'} ---")
    return ok

def hard_fail_missing_seats():
    """Raise by returning False on any missing canonical seat."""
    missing = [n for n in CANON_SEATS if bpy.data.objects.get(n) is None]
    if missing:
        print("ABORT: missing canonical seats:", missing)
        return False
    return True

################################################################################
# SECTION 2: RESET — Full scene reset to canonical state
# Every C script must call this first. No script depends on any other.
################################################################################
def reset_scene_to_canonical():
    """Reset ALL objects to canonical positions. No script should depend on
    any other — each script calls this first and sets its own starting state."""

    all_names = [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
    ]

    # 1. Clear ALL animation data from every relevant object
    for name in all_names:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    # 2. Clear ALL constraints from ball
    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    # 3. Reset ALL hinges to 0 rotation
    for hinge_name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        hinge = bpy.data.objects.get(hinge_name)
        if hinge:
            hinge.rotation_mode = 'XYZ'
            hinge.rotation_euler = (0.0, 0.0, 0.0)

    # 4. Remove stale Seat empties from prior runs
    for seat_name in ["Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)

    bpy.context.view_layer.update()
    print("=== Scene reset to canonical state ===")

################################################################################
# SECTION 3: Helper — set interpolation on a specific keyframe by frame number
################################################################################
def set_last_keyframe_interpolation(obj, data_path, frame, interp='LINEAR'):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    try:
        fcurves = action.fcurves
    except AttributeError:
        try:
            fcurves = action.layers[0].strips[0].channelbag_for_slot(
                action.slots[0]
            ).fcurves
        except Exception:
            print(f"WARNING: Could not access fcurves for {obj.name} — skipping interpolation set")
            return
    for fc in fcurves:
        if fc.data_path == data_path or data_path in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp

################################################################################
# SECTION 4: Helper — key X-axis rotation with LINEAR interpolation
################################################################################
def key_rot_x(obj, frame, degrees):
    bpy.context.scene.frame_set(frame)
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=frame)
    set_last_keyframe_interpolation(obj, "rotation_euler", frame, 'LINEAR')

################################################################################
# SECTION 5: Helper — key constraint influence with CONSTANT interpolation
################################################################################
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

################################################################################
# SECTION 6: Helper — parent preserving world transform
################################################################################
def parent_preserve_world(child, new_parent):
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw

################################################################################
# SECTION 7: Main C12 setup function
################################################################################
def setup_blue_to_red():
    print("=== C12 Start: Blue → Red ===")

    # --- STEP 0: Full scene reset (independence guarantee) ---
    reset_scene_to_canonical()

    # --- 7A: Validate all required objects ---
    blue  = bpy.data.objects.get("Cube_Blue")
    red   = bpy.data.objects.get("Cube_Red")
    ball  = bpy.data.objects.get("Ball")
    hinge = bpy.data.objects.get("Hinge_Blue_Red")

    missing = [n for n, o in [
        ("Cube_Blue",      blue),
        ("Cube_Red",       red),
        ("Ball",           ball),
        ("Hinge_Blue_Red", hinge),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    # --- 7B: Reset hinge rotation ---
    bpy.context.scene.frame_set(F_START)
    hinge.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # --- 7C: Parent Cube_Blue to Hinge_Blue_Red ---
    if blue.parent != hinge:
        parent_preserve_world(blue, hinge)
        print("Cube_Blue parented to Hinge_Blue_Red.")

    # --- 7D: Remove rigid body from ball ---
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            try:
                ball.rigid_body.kinematic = True
            except Exception:
                pass

    bpy.context.view_layer.update()

    # --- 7E/7F: Four-Seat Contract — build ALL 4 canonical seats at Z=0.5 ---
    ensure_four_seats()
    if not validate_four_seats("after ensure_four_seats"):
        print("ABORT: four-seat validation failed at build time.")
        return False
    if not hard_fail_missing_seats():
        return False

    seat_blue = bpy.data.objects.get("Seat_Blue")
    seat_red  = bpy.data.objects.get("Seat_Red")

    # --- 7G: Ball COPY_TRANSFORMS constraints ---
    latch_blue = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_blue.name = "Latch_Blue"
    latch_blue.target = seat_blue
    print("Latch_Blue created.")

    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name = "Latch_Red"
    latch_red.target = seat_red
    print("Latch_Red created — available for reuse by C13.")

    # --- 7H: Keyframe hinge rotation (LINEAR) ---
    key_rot_x(hinge, F_START,   0)
    key_rot_x(hinge, F_MID,    90)
    key_rot_x(hinge, F_HOLD,  180)
    key_rot_x(hinge, F_SWAP,  180)
    key_rot_x(hinge, F_RET,    90)
    key_rot_x(hinge, F_END,     0)
    print("Hinge_Blue_Red rotation keyed — LINEAR.")

    # --- 7I: Keyframe constraint influences (CONSTANT) ---
    key_influence(ball, "Latch_Blue", F_START, 1.0)
    key_influence(ball, "Latch_Red",  F_START, 0.0)
    key_influence(ball, "Latch_Blue", F_HOLD,  1.0)
    key_influence(ball, "Latch_Red",  F_HOLD,  0.0)
    key_influence(ball, "Latch_Blue", F_SWAP,  0.0)
    key_influence(ball, "Latch_Red",  F_SWAP,  1.0)
    key_influence(ball, "Latch_Blue", F_END,   0.0)
    key_influence(ball, "Latch_Red",  F_END,   1.0)
    print("Ball influences keyed — CONSTANT.")

    # --- 7J: Set frame range and reset to F_START ---
    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    validate_four_seats("C12 final")

    print("=== C12 Complete: Blue → Red ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_HOLD}→{F_SWAP}")
    print(f"ROT_SIGN: {ROT_SIGN} | Axis: X | Hinge: Hinge_Blue_Red")
    print(f"Latch_Red left active at influence 1.0 — ready for C13 reuse.")
    return True

################################################################################
# SECTION 8: Blender UI Panel and Operator
################################################################################
class LORQB_PT_C12Panel(bpy.types.Panel):
    bl_label       = "LorQB C12: Blue → Red"
    bl_idname      = "LORQB_PT_c12_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.blue_to_red", text="Run C12: Blue → Red", icon="CONSTRAINT")
        col = layout.column(align=True)
        col.label(text="Transfer: Frame 120 → 121 @ 180°")
        col.separator()
        col.label(text="● Blue → Red → Green → Yellow")

class LORQB_OT_BlueToRed(bpy.types.Operator):
    bl_idname  = "lorqb.blue_to_red"
    bl_label   = "Blue to Red C12"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = setup_blue_to_red()
        if success:
            self.report({'INFO'}, "C12 complete: Blue → Red")
        else:
            self.report({'ERROR'}, "C12 failed — check console")
        return {'FINISHED'}

################################################################################
# SECTION 9: Register / Unregister
################################################################################
def _unregister_all_lorqb():
    to_remove = []
    for name in dir(bpy.types):
        cls = getattr(bpy.types, name, None)
        if cls is None:
            continue
        bl_idname = getattr(cls, "bl_idname", "") or ""
        if "lorqb" in bl_idname.lower():
            to_remove.append(cls)
    for cls in to_remove:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

def register():
    _unregister_all_lorqb()
    bpy.utils.register_class(LORQB_PT_C12Panel)
    bpy.utils.register_class(LORQB_OT_BlueToRed)
    print("\n" + "=" * 50)
    print("✓ LorQB C12 Panel Ready.")
    print("3D View → N-panel → LorQB → 'Run C12: Blue → Red'")
    print("=" * 50 + "\n")

def unregister():
    try:
        bpy.utils.unregister_class(LORQB_OT_BlueToRed)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(LORQB_PT_C12Panel)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()