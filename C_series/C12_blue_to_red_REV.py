# ============================================================================
# C12_blue_to_red_REV.py  (Blender 5.0.1)
# C12_REV — Red → Blue  (return to base)
# Frames 1 – 240 | Transfer at frame 120 → 121
# Chain: Blue — Red — Green — Yellow
# Hinge: Hinge_Blue_Red (X-axis rotation, ROT_SIGN = +1.0) — same as C12
# Ball rides Cube_Red (Latch_Red) → returns to Cube_Blue (Latch_Blue)
# Same hinge and rotation as C12. Ball direction is reversed.
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

SEAT_BLUE_WORLD = mathutils.Vector((0.51, 0.51, 0.25))

################################################################################
# SECTION 2: RESET — Full scene reset to canonical state
################################################################################
def reset_scene_to_canonical():
    all_names = [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
    ]

    for name in all_names:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    for hinge_name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        hinge = bpy.data.objects.get(hinge_name)
        if hinge:
            hinge.rotation_mode = 'XYZ'
            hinge.rotation_euler = (0.0, 0.0, 0.0)

    for seat_name in ["Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)

    bpy.context.view_layer.update()
    print("=== Scene reset to canonical state ===")

################################################################################
# SECTION 3: Helper — set interpolation on a specific keyframe
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
# SECTION 7: Main C12_REV setup function
################################################################################
def setup_red_to_blue():
    print("=== C12_REV Start: Red → Blue ===")

    reset_scene_to_canonical()

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

    # --- Move ball to Red's seat before animating ---
    bpy.context.scene.frame_set(F_START)
    ball.location = SEAT_BLUE_WORLD  # temporary; overridden by constraints below
    hinge.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # --- Parent Cube_Blue to Hinge_Blue_Red (same as C12) ---
    if blue.parent != hinge:
        parent_preserve_world(blue, hinge)
        print("Cube_Blue parented to Hinge_Blue_Red.")

    # --- Remove rigid body from ball ---
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

    # --- Seat_Red: ball starts here (Red's interior) ---
    ball_world       = mathutils.Vector((0.51, -0.51, 0.25))
    seat_red_local   = red.matrix_world.inverted() @ ball_world
    print(f"Seat_Red world (start): {ball_world[:]}")
    print(f"Seat_Red local: {seat_red_local[:]}")

    seat_red = bpy.data.objects.new("Seat_Red", None)
    seat_red.empty_display_type = 'SPHERE'
    seat_red.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_red)
    seat_red.parent = red
    seat_red.location = seat_red_local
    print("Seat_Red created inside Cube_Red.")

    # --- Seat_Blue: ball lands here after return ---
    seat_blue_local = blue.matrix_world.inverted() @ SEAT_BLUE_WORLD
    print(f"Seat_Blue world (target): {SEAT_BLUE_WORLD[:]}")
    print(f"Seat_Blue local: {seat_blue_local[:]}")

    seat_blue = bpy.data.objects.new("Seat_Blue", None)
    seat_blue.empty_display_type = 'SPHERE'
    seat_blue.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue)
    seat_blue.parent = blue
    seat_blue.location = seat_blue_local
    print("Seat_Blue created inside Cube_Blue.")

    bpy.context.view_layer.update()

    # --- Ball constraints: Red first, Blue second ---
    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name = "Latch_Red"
    latch_red.target = seat_red
    print("Latch_Red created.")

    latch_blue = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_blue.name = "Latch_Blue"
    latch_blue.target = seat_blue
    print("Latch_Blue created.")

    # --- Hinge rotation: same as C12 (0 → 180 → 0) ---
    key_rot_x(hinge, F_START,   0)
    key_rot_x(hinge, F_MID,    90)
    key_rot_x(hinge, F_HOLD,  180)
    key_rot_x(hinge, F_SWAP,  180)
    key_rot_x(hinge, F_RET,    90)
    key_rot_x(hinge, F_END,     0)
    print("Hinge_Blue_Red rotation keyed — LINEAR.")

    # --- Ball transfer: Red → Blue at F_SWAP ---
    key_influence(ball, "Latch_Red",  F_START, 1.0)
    key_influence(ball, "Latch_Blue", F_START, 0.0)
    key_influence(ball, "Latch_Red",  F_HOLD,  1.0)
    key_influence(ball, "Latch_Blue", F_HOLD,  0.0)
    key_influence(ball, "Latch_Red",  F_SWAP,  0.0)
    key_influence(ball, "Latch_Blue", F_SWAP,  1.0)
    key_influence(ball, "Latch_Red",  F_END,   0.0)
    key_influence(ball, "Latch_Blue", F_END,   1.0)
    print("Ball influences keyed — CONSTANT.")

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C12_REV Complete: Red → Blue ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_HOLD}→{F_SWAP}")
    print(f"ROT_SIGN: {ROT_SIGN} | Axis: X | Hinge: Hinge_Blue_Red")
    return True

################################################################################
# SECTION 8: Blender UI Panel and Operator
################################################################################
class LORQB_OT_ResetC12REV(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c12_rev"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "Reset to base complete")
        return {'FINISHED'}

class LORQB_PT_C12REVPanel(bpy.types.Panel):
    bl_label       = "LorQB C12_REV: Red → Blue"
    bl_idname      = "LORQB_PT_c12_rev_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c12_rev", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.red_to_blue", text="Run C12_REV: Red → Blue", icon="CONSTRAINT")
        col = layout.column(align=True)
        col.label(text="Transfer: Frame 120 → 121 @ 180°")
        col.separator()
        col.label(text="● Red → Blue (return to base)")

class LORQB_OT_RedToBlue(bpy.types.Operator):
    bl_idname  = "lorqb.red_to_blue"
    bl_label   = "Red to Blue C12_REV"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = setup_red_to_blue()
        if success:
            self.report({'INFO'}, "C12_REV complete: Red → Blue")
        else:
            self.report({'ERROR'}, "C12_REV failed — check console")
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
    bpy.utils.register_class(LORQB_OT_ResetC12REV)
    bpy.utils.register_class(LORQB_PT_C12REVPanel)
    bpy.utils.register_class(LORQB_OT_RedToBlue)
    print("\n" + "=" * 50)
    print("✓ LorQB C12_REV Panel Ready.")
    print("3D View → N-panel → LorQB → 'Run C12_REV: Red → Blue'")
    print("=" * 50 + "\n")

def unregister():
    for cls in [LORQB_OT_RedToBlue, LORQB_PT_C12REVPanel, LORQB_OT_ResetC12REV]:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
