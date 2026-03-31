# ============================================================================
# C15_yellow_to_blue.py  (Blender 5.0.1)
# C15 — Yellow → Blue
# Frames 720 – 960 | Transfer at frame 840 → 841
# Chain: Blue — Red — Green — Yellow
# Hinge: Hinge_Red_Green (Y-axis rotation, ROT_SIGN = +1.0)
# Ball rides Cube_Yellow (Latch_Yellow) → drops into Cube_Blue (Latch_Blue)
# Green+Yellow swing as one unit toward Blue+Red — ball deposits into Blue
# Architecture: matches C12/C13 reference standard
# ============================================================================

import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
################################################################################
F_START = 720   # Start: Green+Yellow at 0°, ball in Yellow
F_MID   = 780   # Mid:   Hinge at 90°
F_HOLD  = 840   # Hold:  Hinge at 180° — ball aligned above Blue
F_SWAP  = 841   # Swap:  ball transfers from Latch_Yellow to Latch_Blue
F_RET   = 900   # Return: Hinge at 90° on way back
F_END   = 960   # End:   Hinge at 0°, ball in Blue

ROT_AXIS = 1        # Y-axis index in rotation_euler
ROT_SIGN = +1.0     # Positive Y rotation swings Green+Yellow toward Blue

SEAT_YELLOW_WORLD = mathutils.Vector((-0.51,  0.51, 0.25))
SEAT_BLUE_WORLD   = mathutils.Vector(( 0.51,  0.51, 0.25))

################################################################################
# SECTION 2: RESET — Full scene reset to canonical state
# Every C script must call this first. No script depends on any other.
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
# SECTION 7: Main C15 setup function
################################################################################
def setup_yellow_to_blue():
    print("=== C15 Start: Yellow → Blue ===")

    # --- STEP 0: Full scene reset (independence guarantee) ---
    reset_scene_to_canonical()

    # --- 7A: Validate all required objects ---
    hinge  = bpy.data.objects.get("Hinge_Red_Green")
    ball   = bpy.data.objects.get("Ball")
    yellow = bpy.data.objects.get("Cube_Yellow")
    green  = bpy.data.objects.get("Cube_Green")
    blue   = bpy.data.objects.get("Cube_Blue")
    red    = bpy.data.objects.get("Cube_Red")

    missing = [n for n, o in [
        ("Hinge_Red_Green", hinge),
        ("Ball",            ball),
        ("Cube_Yellow",     yellow),
        ("Cube_Green",      green),
        ("Cube_Blue",       blue),
        ("Cube_Red",        red),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    # --- 7B: Reset hinge rotation ---
    bpy.context.scene.frame_set(F_START)
    hinge.rotation_mode = 'XYZ'
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # --- 7C: Parent Yellow to Green, Green to Hinge_Red_Green ---
    parent_preserve_world(yellow, green)
    print("Cube_Yellow parented to Cube_Green — passive carry.")
    parent_preserve_world(green, hinge)
    print("Cube_Green parented to Hinge_Red_Green — active arm.")
    bpy.context.view_layer.update()

    # --- 7D: Create Seat_Yellow empty parented to Cube_Yellow ---
    seat_yellow_local = yellow.matrix_world.inverted() @ SEAT_YELLOW_WORLD
    print(f"Seat_Yellow world (target): {SEAT_YELLOW_WORLD[:]}")
    print(f"Seat_Yellow local (converted): {seat_yellow_local[:]}")

    seat_yellow = bpy.data.objects.new("Seat_Yellow", None)
    seat_yellow.empty_display_type = 'SPHERE'
    seat_yellow.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_yellow)
    seat_yellow.parent = yellow
    seat_yellow.location = seat_yellow_local
    print("Seat_Yellow created inside Cube_Yellow.")

    # --- 7E: Create Seat_Blue empty parented to Cube_Blue ---
    seat_blue_local = blue.matrix_world.inverted() @ SEAT_BLUE_WORLD
    print(f"Seat_Blue world (target): {SEAT_BLUE_WORLD[:]}")
    print(f"Seat_Blue local (converted): {seat_blue_local[:]}")

    seat_blue = bpy.data.objects.new("Seat_Blue", None)
    seat_blue.empty_display_type = 'SPHERE'
    seat_blue.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue)
    seat_blue.parent = blue
    seat_blue.location = seat_blue_local
    print("Seat_Blue created inside Cube_Blue.")

    bpy.context.view_layer.update()
    print(f"Seat_Yellow world actual: {seat_yellow.matrix_world.translation[:]}")
    print(f"Seat_Blue   world actual: {seat_blue.matrix_world.translation[:]}")

    # --- 7F: Ball COPY_TRANSFORMS constraints ---
    latch_yellow = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_yellow.name = "Latch_Yellow"
    latch_yellow.target = seat_yellow
    print("Latch_Yellow created.")

    latch_blue = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_blue.name = "Latch_Blue"
    latch_blue.target = seat_blue
    print("Latch_Blue created.")

    # --- 7G: Keyframe hinge rotation (LINEAR) ---
    key_rot_y(hinge, F_START,   0)
    key_rot_y(hinge, F_MID,    90)
    key_rot_y(hinge, F_HOLD,  180)
    key_rot_y(hinge, F_SWAP,  180)
    key_rot_y(hinge, F_RET,    90)
    key_rot_y(hinge, F_END,     0)
    print("Hinge_Red_Green rotation keyed — LINEAR.")

    # --- 7H: Keyframe constraint influences (CONSTANT) ---
    key_influence(ball, "Latch_Yellow", F_START, 1.0)
    key_influence(ball, "Latch_Blue",   F_START, 0.0)
    key_influence(ball, "Latch_Yellow", F_HOLD,  1.0)
    key_influence(ball, "Latch_Blue",   F_HOLD,  0.0)
    key_influence(ball, "Latch_Yellow", F_SWAP,  0.0)
    key_influence(ball, "Latch_Blue",   F_SWAP,  1.0)
    key_influence(ball, "Latch_Yellow", F_END,   0.0)
    key_influence(ball, "Latch_Blue",   F_END,   1.0)
    print("Ball influences keyed — CONSTANT.")

    # --- 7I: Set frame range and reset to F_START ---
    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C15 Complete: Yellow → Blue ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_HOLD}→{F_SWAP}")
    print(f"ROT_SIGN: {ROT_SIGN} | Axis: Y | Hinge: Hinge_Red_Green")
    print("Green+Yellow swing together toward Blue+Red.")
    return True

################################################################################
# SECTION 8: Blender UI Panel and Operator
################################################################################
class LORQB_OT_ResetC15(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c15"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "Reset to base complete")
        return {'FINISHED'}

class LORQB_PT_C15Panel(bpy.types.Panel):
    bl_label       = "LorQB C15: Yellow → Blue"
    bl_idname      = "LORQB_PT_c15_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c15", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.yellow_to_blue", text="Run C15: Yellow → Blue", icon="CONSTRAINT")
        col = layout.column(align=True)
        col.label(text="Transfer: Frame 840 → 841 @ 180°")
        col.separator()
        col.label(text="● Blue → Red → Green → Yellow")
        col.label(text="Green+Yellow swing toward Blue+Red")

class LORQB_OT_YellowToBlue(bpy.types.Operator):
    bl_idname  = "lorqb.yellow_to_blue"
    bl_label   = "Yellow to Blue C15"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = setup_yellow_to_blue()
        if success:
            self.report({'INFO'}, "C15 complete: Yellow → Blue")
        else:
            self.report({'ERROR'}, "C15 failed — check console")
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
    bpy.utils.register_class(LORQB_OT_ResetC15)
    bpy.utils.register_class(LORQB_PT_C15Panel)
    bpy.utils.register_class(LORQB_OT_YellowToBlue)
    print("\n" + "=" * 50)
    print("✓ LorQB C15 Panel Ready.")
    print("3D View → N-panel → LorQB → 'Run C15: Yellow → Blue'")
    print("=" * 50 + "\n")

def unregister():
    try:
        bpy.utils.unregister_class(LORQB_OT_YellowToBlue)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(LORQB_PT_C15Panel)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(LORQB_OT_ResetC15)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
