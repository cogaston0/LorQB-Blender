# ============================================================================
# C14_green_to_yellow.py  (Blender 5.0.1)
# C14 — Green → Yellow
# Frames 481 – 720 | Transfer at frame 600 → 601
# Chain: Blue — Red — Green — Yellow
# Hinge: Hinge_Green_Yellow (X-axis rotation, ROT_SIGN = +1.0)
# Ball rides Cube_Green (Latch_Green) → drops into Cube_Yellow (Latch_Yellow)
# Blue + Red + Hinge_Blue_Red + Hinge_Red_Green ride passively with Green.
# Only Hinge_Green_Yellow is keyed. No other hinges are touched.
# Architecture: matches C12/C13 reference standard
# ============================================================================

import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
################################################################################
F_START = 481   # Start: Green at 0°, ball in Green
F_MID   = 540   # Mid:   Green at 90°
F_HOLD  = 600   # Hold:  Green at 180° — ball aligned above Yellow
F_SWAP  = 601   # Swap:  ball transfers from Latch_Green to Latch_Yellow
F_RET   = 660   # Return: Green at 90° on way back
F_END   = 720   # End:   Green at 0°, ball in Yellow

ROT_AXIS = 0        # X-axis index in rotation_euler
ROT_SIGN = +1.0     # Positive X rotation — flip if backwards

SEAT_GREEN_WORLD  = mathutils.Vector((-0.51, -0.51, 0.25))
SEAT_YELLOW_WORLD = mathutils.Vector((-0.51,  0.51, 0.25))

################################################################################
# SECTION 2: RESET — Clear only Hinge_Green_Yellow and ball state.
# Blue, Red, Hinge_Blue_Red, Hinge_Red_Green are NOT touched —
# they ride passively as part of the physical rig attached to Green.
################################################################################
def reset_c14_state():
    hinge = bpy.data.objects.get("Hinge_Green_Yellow")
    if hinge and hinge.animation_data:
        hinge.animation_data_clear()

    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    for seat_name in ["Seat_Green", "Seat_Yellow"]:
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)

    # Zero hinge rotation (animation_data_clear freezes it at current angle)
    if hinge:
        hinge.rotation_mode  = 'XYZ'
        hinge.rotation_euler = (0.0, 0.0, 0.0)

    bpy.context.view_layer.update()

    # Unparent Green and restore canonical position
    green = bpy.data.objects.get("Cube_Green")
    if green:
        if green.animation_data:
            green.animation_data_clear()
        green.parent = None
        bpy.context.view_layer.update()
        green.location       = (-0.51, 0.0, 1.0)
        green.rotation_mode  = 'XYZ'
        green.rotation_euler = (0.0, 0.0, 0.0)

    bpy.context.view_layer.update()
    print("=== C14 reset: hinge zeroed, Green unparented and repositioned ===")

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
# SECTION 7: Main C14 setup function
################################################################################
def setup_green_to_yellow():
    print("=== C14 Start: Green → Yellow ===")

    reset_c14_state()

    green  = bpy.data.objects.get("Cube_Green")
    yellow = bpy.data.objects.get("Cube_Yellow")
    ball   = bpy.data.objects.get("Ball")
    hinge  = bpy.data.objects.get("Hinge_Green_Yellow")

    missing = [n for n, o in [
        ("Cube_Green",         green),
        ("Cube_Yellow",        yellow),
        ("Ball",               ball),
        ("Hinge_Green_Yellow", hinge),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    bpy.context.scene.frame_set(F_START)
    hinge.rotation_mode = 'XYZ'
    hinge.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # Parent Green to Hinge_Green_Yellow only — Blue/Red ride with the rig
    if green.parent != hinge:
        parent_preserve_world(green, hinge)
        print("Green parented to Hinge_Green_Yellow.")
    else:
        print("Green already parented to Hinge_Green_Yellow — skipped.")

    bpy.context.view_layer.update()

    seat_green_local = green.matrix_world.inverted() @ SEAT_GREEN_WORLD
    print(f"Seat_Green world (target): {SEAT_GREEN_WORLD[:]}")
    print(f"Seat_Green local (converted): {seat_green_local[:]}\n")
    seat_green = bpy.data.objects.new("Seat_Green", None)
    seat_green.empty_display_type = 'SPHERE'
    seat_green.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_green)
    seat_green.parent = green
    seat_green.location = seat_green_local
    print("Seat_Green created inside Cube_Green.")

    seat_yellow_local = yellow.matrix_world.inverted() @ SEAT_YELLOW_WORLD
    print(f"Seat_Yellow world (target): {SEAT_YELLOW_WORLD[:]}")
    print(f"Seat_Yellow local (converted): {seat_yellow_local[:]}\n")
    seat_yellow = bpy.data.objects.new("Seat_Yellow", None)
    seat_yellow.empty_display_type = 'SPHERE'
    seat_yellow.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_yellow)
    seat_yellow.parent = yellow
    seat_yellow.location = seat_yellow_local
    print("Seat_Yellow created inside Cube_Yellow.")

    bpy.context.view_layer.update()
    print(f"Seat_Green  world actual: {seat_green.matrix_world.translation[:]}")
    print(f"Seat_Yellow world actual: {seat_yellow.matrix_world.translation[:]}\n")

    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name = "Latch_Green"
    latch_green.target = seat_green
    print("Latch_Green created.")

    latch_yellow = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_yellow.name = "Latch_Yellow"
    latch_yellow.target = seat_yellow
    print("Latch_Yellow created.")

    # Only Hinge_Green_Yellow is keyed — Blue/Red/Hinge_Blue_Red/Hinge_Red_Green NOT touched
    key_rot_x(hinge, F_START,   0)
    key_rot_x(hinge, F_MID,    90)
    key_rot_x(hinge, F_HOLD,  180)
    key_rot_x(hinge, F_SWAP,  180)
    key_rot_x(hinge, F_RET,    90)
    key_rot_x(hinge, F_END,     0)
    print("Hinge_Green_Yellow rotation keyed — LINEAR.")

    key_influence(ball, "Latch_Green",  F_START, 1.0)
    key_influence(ball, "Latch_Yellow", F_START, 0.0)
    key_influence(ball, "Latch_Green",  F_HOLD,  1.0)
    key_influence(ball, "Latch_Yellow", F_HOLD,  0.0)
    key_influence(ball, "Latch_Green",  F_SWAP,  0.0)
    key_influence(ball, "Latch_Yellow", F_SWAP,  1.0)
    key_influence(ball, "Latch_Green",  F_END,   0.0)
    key_influence(ball, "Latch_Yellow", F_END,   1.0)
    print("Ball influences keyed — CONSTANT.")

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C14 Complete: Green → Yellow ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_HOLD}→{F_SWAP}")
    print(f"ROT_SIGN: {ROT_SIGN} | Axis: X | Hinge: Hinge_Green_Yellow")
    print("Blue + Red ride passively — Hinge_Blue_Red + Hinge_Red_Green NOT keyed.")
    return True

################################################################################
# SECTION 8: Blender UI Panel and Operator
################################################################################
class LORQB_OT_ResetC14(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c14"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_c14_state()
        self.report({'INFO'}, "Reset to base complete")
        return {'FINISHED'}

class LORQB_PT_C14Panel(bpy.types.Panel):
    bl_label       = "LorQB C14: Green → Yellow"
    bl_idname      = "LORQB_PT_c14_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c14", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.green_to_yellow", text="Run C14: Green → Yellow", icon="CONSTRAINT")
        col = layout.column(align=True)
        col.label(text="Transfer: Frame 600 → 601 @ 180°")
        col.separator()
        col.label(text="● Blue → Red → Green → Yellow")
        col.label(text="Only Hinge_Green_Yellow rotates")

class LORQB_OT_GreenToYellow(bpy.types.Operator):
    bl_idname  = "lorqb.green_to_yellow"
    bl_label   = "Green to Yellow C14"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = setup_green_to_yellow()
        if success:
            self.report({'INFO'}, "C14 complete: Green → Yellow")
        else:
            self.report({'ERROR'}, "C14 failed — check console")
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
    bpy.utils.register_class(LORQB_OT_ResetC14)
    bpy.utils.register_class(LORQB_PT_C14Panel)
    bpy.utils.register_class(LORQB_OT_GreenToYellow)
    print("\n" + "=" * 50)
    print("✓ LorQB C14 Panel Ready.")
    print("3D View → N-panel → LorQB → 'Run C14: Green → Yellow'")
    print("=" * 50 + "\n")

def unregister():
    try:
        bpy.utils.unregister_class(LORQB_OT_GreenToYellow)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(LORQB_PT_C14Panel)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(LORQB_OT_ResetC14)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()