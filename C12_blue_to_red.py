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

# Blue seat is defined in Cube_Blue LOCAL space — derived from Blue itself,
# never guessed as a world constant. Red target remains world-based (verified).
SEAT_BLUE_LOCAL = mathutils.Vector((0.0, 0.0, 0.25))
SEAT_RED_WORLD  = mathutils.Vector((0.51, -0.51, 0.25))

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
    fcurves = None
    try:
        fcurves = action.fcurves
    except AttributeError:
        pass
    if fcurves is None:
        try:
            fcurves = action.layers[0].strips[0].channelbag_for_slot(action.slots[0]).fcurves
        except Exception:
            pass
    if fcurves is None:
        try:
            fcurves = action.layers[0].strips[0].channelbags[0].fcurves
        except Exception:
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

    # --- 7E: Create Seat_Blue empty parented to Cube_Blue ---
    # Blue seat is anchored in Cube_Blue LOCAL space.
    # Do NOT derive from Ball's scene position and do NOT use a guessed world constant.
    # World position is computed from Blue's actual transform at frame 1.
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()

    seat_blue_world = blue.matrix_world @ SEAT_BLUE_LOCAL
    print(f"Cube_Blue world pos:      {blue.matrix_world.translation[:]}")
    print(f"Seat_Blue local (fixed):  {SEAT_BLUE_LOCAL[:]}")
    print(f"Seat_Blue world (derived):{seat_blue_world[:]}")

    seat_blue = bpy.data.objects.new("Seat_Blue", None)
    seat_blue.empty_display_type = 'SPHERE'
    seat_blue.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue)
    seat_blue.parent = blue
    seat_blue.location = SEAT_BLUE_LOCAL.copy()
    print("Seat_Blue created inside Cube_Blue (local-space anchored).")

    # --- 7E.1: Force Ball to derived Blue seat BEFORE constraints are keyed ---
    # This guarantees frame 1 shows Ball inside Blue regardless of prior state.
    ball.matrix_world.translation = seat_blue_world.copy()
    bpy.context.view_layer.update()
    print(f"Ball forced to Blue seat: {ball.matrix_world.translation[:]}")

    # --- 7F: Create Seat_Red empty parented to Cube_Red ---
    seat_red_local = red.matrix_world.inverted() @ SEAT_RED_WORLD
    print(f"Seat_Red world (target): {SEAT_RED_WORLD[:]}")
    print(f"Seat_Red local (converted): {seat_red_local[:]}")

    seat_red = bpy.data.objects.new("Seat_Red", None)
    seat_red.empty_display_type = 'SPHERE'
    seat_red.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_red)
    seat_red.parent = red
    seat_red.location = seat_red_local
    print("Seat_Red created inside Cube_Red.")

    bpy.context.view_layer.update()
    print(f"Seat_Blue world actual: {seat_blue.matrix_world.translation[:]}")
    print(f"Seat_Red  world actual: {seat_red.matrix_world.translation[:]}")

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

    print("=== C12 Complete: Blue → Red ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_HOLD}→{F_SWAP}")
    print(f"ROT_SIGN: {ROT_SIGN} | Axis: X | Hinge: Hinge_Blue_Red")
    print(f"Latch_Red left active at influence 1.0 — ready for C13 reuse.")
    return True

################################################################################
# SECTION 8: Blender UI Panel and Operator
################################################################################
class LORQB_OT_ResetC12(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c12"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "Reset to base complete")
        return {'FINISHED'}

class LORQB_PT_C12Panel(bpy.types.Panel):
    bl_label       = "LorQB C12: Blue → Red"
    bl_idname      = "LORQB_PT_c12_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c12", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.blue_to_red", text="Run C12: Blue → Red", icon='PLAY')

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
    bpy.utils.register_class(LORQB_OT_ResetC12)
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
    try:
        bpy.utils.unregister_class(LORQB_OT_ResetC12)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()