# ============================================================================
# lorqb_green_to_yellow_C14.py  (Blender 5.1.1)
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
ROT_SIGN = -1.0     # TODO: verify empirically in viewport — never infer from other scripts

SEAT_GREEN_WORLD  = mathutils.Vector((-0.51, -0.51, 0.25))
SEAT_YELLOW_WORLD = mathutils.Vector((-0.51,  0.51, 0.25))

################################################################################
# SECTION 2: RESET — Full standalone scene reset (Rule 2)
# Clears ALL hinges, rebuilds full parent chain, restores canonical positions.
# No assumption is made about state left by any prior script.
################################################################################
def reset_scene_to_canonical():
    all_names = [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
    ]

    # 1. Clear ALL animation data
    for name in all_names:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    # 2. Clear ball constraints
    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    # 3. Reset ALL hinges to 0 rotation
    for hinge_name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        hinge = bpy.data.objects.get(hinge_name)
        if hinge:
            hinge.rotation_mode = 'XYZ'
            hinge.rotation_euler = (0.0, 0.0, 0.0)

    # 4. Remove stale Seat empties
    for seat_name in ["Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)

    # 5. Rebuild canonical parent chain (Rule 6: no topology bypasses)
    # Chain: Hinge_GY → Cube_Green → Hinge_RG → Cube_Red → Hinge_BR → Cube_Blue
    chain = [
        ("Cube_Blue",          "Hinge_Blue_Red"),
        ("Hinge_Blue_Red",     "Cube_Red"),
        ("Cube_Red",           "Hinge_Red_Green"),
        ("Hinge_Red_Green",    "Cube_Green"),
        ("Cube_Green",         "Hinge_Green_Yellow"),
    ]
    for child_name, parent_name in chain:
        child  = bpy.data.objects.get(child_name)
        parent = bpy.data.objects.get(parent_name)
        if child and parent and child.parent != parent:
            mw = child.matrix_world.copy()
            child.parent = parent
            child.matrix_parent_inverse = parent.matrix_world.inverted()
            child.matrix_world = mw
            bpy.context.view_layer.update()
            print(f"  Chain: {child_name} → {parent_name}")

    # 6. Restore canonical world positions
    canonical_positions = {
        "Cube_Blue":          (0.51,  0.51,  0.25),
        "Cube_Red":           (0.51, -0.51,  0.25),
        "Cube_Green":         (-0.51, -0.51, 0.25),
        "Cube_Yellow":        (-0.51,  0.51,  0.25),
        "Hinge_Blue_Red":     (0.51,  0.0,   1.0),
        "Hinge_Red_Green":    (0.0,  -0.51,  1.0),
        "Hinge_Green_Yellow": (-0.51,  0.0,   1.0),
    }
    for obj_name, pos in canonical_positions.items():
        obj = bpy.data.objects.get(obj_name)
        if obj:
            obj.location = mathutils.Vector(pos)
    bpy.context.view_layer.update()

    print("=== C14 scene reset to canonical state ===")

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

    reset_scene_to_canonical()

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

    # --- 7B: Reset hinge rotation ---
    bpy.context.scene.frame_set(F_START)
    hinge.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # --- 7C: Parent Cube_Green to Hinge_Green_Yellow ---
    if green.parent != hinge:
        parent_preserve_world(green, hinge)
        print("Cube_Green parented to Hinge_Green_Yellow.")

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

    # --- 7E: Create Seat_Green empty parented to Cube_Green ---
    # Seat_Green captured from ball's actual world position (Rule 3)
    ball_world = ball.matrix_world.translation.copy()
    seat_green_local = green.matrix_world.inverted() @ ball_world
    print(f"Ball world pos: {ball_world[:]}")
    print(f"Seat_Green world (target): {SEAT_GREEN_WORLD[:]}")
    print(f"Seat_Green local (converted): {seat_green_local[:]}\n")
    seat_green = bpy.data.objects.new("Seat_Green", None)
    seat_green.empty_display_type = 'SPHERE'
    seat_green.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_green)
    seat_green.parent = green
    seat_green.location = seat_green_local
    print("Seat_Green created inside Cube_Green.")

    # --- 7F: Create Seat_Yellow empty parented to Cube_Yellow ---
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
    print(f"Seat_Yellow world actual: {seat_yellow.matrix_world.translation[:]}")

    # --- 7G: Ball COPY_TRANSFORMS constraints ---
    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name = "Latch_Green"
    latch_green.target = seat_green
    print("Latch_Green created.")

    latch_yellow = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_yellow.name = "Latch_Yellow"
    latch_yellow.target = seat_yellow
    print("Latch_Yellow created — available for reuse by C15.")

    # --- 7H: Keyframe hinge rotation (LINEAR) ---
    key_rot_x(hinge, F_START,   0)
    key_rot_x(hinge, F_MID,    90)
    key_rot_x(hinge, F_HOLD,  180)
    key_rot_x(hinge, F_SWAP,  180)
    key_rot_x(hinge, F_RET,    90)
    key_rot_x(hinge, F_END,     0)
    print("Hinge_Green_Yellow rotation keyed — LINEAR.")

    # --- 7I: Keyframe constraint influences (CONSTANT) ---
    key_influence(ball, "Latch_Green",  F_START, 1.0)
    key_influence(ball, "Latch_Yellow", F_START, 0.0)
    key_influence(ball, "Latch_Green",  F_HOLD,  1.0)
    key_influence(ball, "Latch_Yellow", F_HOLD,  0.0)
    key_influence(ball, "Latch_Green",  F_SWAP,  0.0)
    key_influence(ball, "Latch_Yellow", F_SWAP,  1.0)
    key_influence(ball, "Latch_Green",  F_END,   0.0)
    key_influence(ball, "Latch_Yellow", F_END,   1.0)
    print("Ball influences keyed — CONSTANT.")

    # --- 7J: Set frame range, reset to F_START ---
    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C14 Complete: Green → Yellow ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_HOLD}→{F_SWAP}")
    print(f"ROT_SIGN: {ROT_SIGN} | Axis: X | Hinge: Hinge_Green_Yellow")
    print(f"Latch_Yellow left active at influence 1.0 — ready for C15 reuse.")
    return True

################################################################################
# SECTION 8: Blender UI Panel and Operator
################################################################################
class LORQB_OT_ResetC14(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c14"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_scene_to_canonical()
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