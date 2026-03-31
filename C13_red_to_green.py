# ============================================================================
# C13_red_to_green.py  (Blender 5.0.1)
# C13 — Red → Green
# Frames 241 – 480 | Transfer at frame 360 → 361
# Chain: Blue — Red — Green — Yellow
# Hinge: Hinge_Red_Green (Y-axis rotation, ROT_SIGN = -1.0)
# Ball rides Cube_Red (Latch_Red) → drops into Cube_Green (Latch_Green)
# Architecture: matches C12 reference standard
# ============================================================================

import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
################################################################################
F_START = 241   # Start: Red at 0°, ball in Red
F_MID   = 300   # Mid:   Red at 90°
F_HOLD  = 360   # Hold:  Red at 180° — ball aligned above Green
F_SWAP  = 361   # Swap:  ball transfers from Latch_Red to Latch_Green
F_RET   = 420   # Return: Red at 90° on way back
F_END   = 480   # End:   Red at 0°, ball in Green

ROT_AXIS = 1        # Y-axis index in rotation_euler
ROT_SIGN = -1.0     # Negative Y rotation swings Red correctly over Green

SEAT_RED_WORLD   = mathutils.Vector((0.51,  -0.51, 0.25))
SEAT_GREEN_WORLD = mathutils.Vector((-0.51, -0.51, 0.25))

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
# SECTION 4: Helper — key Y-axis rotation with LINEAR interpolation
################################################################################
def key_rot_y(obj, frame, degrees):
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
# SECTION 7: Main C13 setup function
################################################################################
def setup_red_to_green():
    print("=== C13 Start: Red → Green ===")

    reset_scene_to_canonical()

    red      = bpy.data.objects.get("Cube_Red")
    green    = bpy.data.objects.get("Cube_Green")
    blue     = bpy.data.objects.get("Cube_Blue")
    ball     = bpy.data.objects.get("Ball")
    hinge_rg = bpy.data.objects.get("Hinge_Red_Green")

    missing = [n for n, o in [
        ("Cube_Red",        red),
        ("Cube_Green",      green),
        ("Cube_Blue",       blue),
        ("Ball",            ball),
        ("Hinge_Red_Green", hinge_rg),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    bpy.context.scene.frame_set(F_START)
    hinge_rg.rotation_mode = 'XYZ'
    hinge_rg.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    if blue.parent != red:
        parent_preserve_world(blue, red)
        print("Blue parented to Red — passive carry.")

    if red.parent != hinge_rg:
        parent_preserve_world(red, hinge_rg)
        print("Red parented to Hinge_Red_Green.")

    bpy.context.view_layer.update()

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

    seat_green_local = green.matrix_world.inverted() @ SEAT_GREEN_WORLD
    print(f"Seat_Green world (target): {SEAT_GREEN_WORLD[:]}")
    print(f"Seat_Green local (converted): {seat_green_local[:]}")

    seat_green = bpy.data.objects.new("Seat_Green", None)
    seat_green.empty_display_type = 'SPHERE'
    seat_green.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_green)
    seat_green.parent = green
    seat_green.location = seat_green_local
    print("Seat_Green created inside Cube_Green.")

    bpy.context.view_layer.update()
    print(f"Seat_Red   world actual: {seat_red.matrix_world.translation[:]}")
    print(f"Seat_Green world actual: {seat_green.matrix_world.translation[:]}")

    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name = "Latch_Red"
    latch_red.target = seat_red
    print("Latch_Red created.")

    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name = "Latch_Green"
    latch_green.target = seat_green
    print("Latch_Green created — available for reuse by C14.")

    key_rot_y(hinge_rg, F_START,   0)
    key_rot_y(hinge_rg, F_MID,    90)
    key_rot_y(hinge_rg, F_HOLD,  180)
    key_rot_y(hinge_rg, F_SWAP,  180)
    key_rot_y(hinge_rg, F_RET,    90)
    key_rot_y(hinge_rg, F_END,     0)
    print("Hinge_Red_Green rotation keyed — LINEAR.")

    key_influence(ball, "Latch_Red",   F_START, 1.0)
    key_influence(ball, "Latch_Green", F_START, 0.0)
    key_influence(ball, "Latch_Red",   F_HOLD,  1.0)
    key_influence(ball, "Latch_Green", F_HOLD,  0.0)
    key_influence(ball, "Latch_Red",   F_SWAP,  0.0)
    key_influence(ball, "Latch_Green", F_SWAP,  1.0)
    key_influence(ball, "Latch_Red",   F_END,   0.0)
    key_influence(ball, "Latch_Green", F_END,   1.0)
    print("Ball influences keyed — CONSTANT.")

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C13 Complete: Red → Green ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_HOLD}→{F_SWAP}")
    print(f"ROT_SIGN: {ROT_SIGN} | Axis: Y | Hinge: Hinge_Red_Green")
    print(f"Latch_Green left active at influence 1.0 — ready for C14 reuse.")
    return True

################################################################################
# SECTION 8: Blender UI Panel and Operator
################################################################################
class LORQB_OT_ResetC13(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c13"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "Reset to base complete")
        return {'FINISHED'}

class LORQB_PT_C13Panel(bpy.types.Panel):
    bl_label       = "LorQB C13: Red → Green"
    bl_idname      = "LORQB_PT_c13_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c13", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.red_to_green", text="Run C13: Red → Green", icon="CONSTRAINT")
        col = layout.column(align=True)
        col.label(text="Transfer: Frame 360 → 361 @ 180°")
        col.separator()
        col.label(text="● Blue → Red → Green → Yellow")
        col.label(text="Blue rides Red — passive carry")

class LORQB_OT_RedToGreen(bpy.types.Operator):
    bl_idname  = "lorqb.red_to_green"
    bl_label   = "Red to Green C13"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = setup_red_to_green()
        if success:
            self.report({'INFO'}, "C13 complete: Red → Green")
        else:
            self.report({'ERROR'}, "C13 failed — check console")
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
    bpy.utils.register_class(LORQB_OT_ResetC13)
    bpy.utils.register_class(LORQB_PT_C13Panel)
    bpy.utils.register_class(LORQB_OT_RedToGreen)
    print("\n" + "=" * 50)
    print("✓ LorQB C13 Panel Ready.")
    print("3D View → N-panel → LorQB → 'Run C13: Red → Green'")
    print("=" * 50 + "\n")

def unregister():
    try:
        bpy.utils.unregister_class(LORQB_OT_RedToGreen)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(LORQB_PT_C13Panel)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(LORQB_OT_ResetC13)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
