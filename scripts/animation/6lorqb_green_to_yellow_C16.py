import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
# Chain: Blue — Red — Green — Yellow
# C16: Ball transfers from Green to Yellow
# Green rotates 180° around Hinge_Green_Yellow (left edge, X-axis)
# Frame range: 481 — 720
# NOTE: Interpolation (LINEAR/CONSTANT) must be set manually in Graph Editor
#       after running this script — same approach as C12/C13.
################################################################################
F_START = 481   # Start: Green at 0°, ball in Green
F_MID   = 540   # Mid:   Green at 90°
F_HOLD  = 600   # Hold:  Green at 180° — ball aligned above Yellow
F_SWAP  = 601   # Swap:  ball transfers from Seat_Green to Seat_Yellow
F_RET   = 660   # Return: Green at 90° on way back
F_END   = 720   # End:   Green at 0°, ball in Yellow

ROT_AXIS = 0        # X-axis index in rotation_euler
ROT_SIGN = 1.0      # Positive X rotation swings Green correctly over Yellow

SEAT_GREEN_WORLD  = mathutils.Vector((-0.51, -0.51, 0.25))
SEAT_YELLOW_WORLD = mathutils.Vector((-0.51,  0.51, 0.25))

################################################################################
# SECTION 2: Helper — parent preserving world transform
################################################################################
def parent_preserve_world(child, new_parent):
    """Parent child to new_parent while keeping child's world transform."""
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw

################################################################################
# SECTION 3: Helper — key X-axis rotation
################################################################################
def key_rot_x(obj, frame, degrees):
    """Insert X-axis rotation keyframe."""
    bpy.context.scene.frame_set(frame)
    obj.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=frame)

################################################################################
# SECTION 4: Helper — key constraint influence
################################################################################
def key_influence(obj, constraint_name, frame, value):
    """Insert constraint influence keyframe."""
    bpy.context.scene.frame_set(frame)
    con = obj.constraints.get(constraint_name)
    if not con:
        print(f"WARNING: Constraint '{constraint_name}' not found on {obj.name}")
        return
    con.influence = value
    obj.keyframe_insert(
        data_path=f'constraints["{constraint_name}"].influence',
        frame=frame
    )

################################################################################
# SECTION 5: Main C16 setup function
################################################################################
def setup_green_to_yellow():

    # --- 5A: Validate required objects ---
    green    = bpy.data.objects.get("Cube_Green")
    yellow   = bpy.data.objects.get("Cube_Yellow")
    ball     = bpy.data.objects.get("Ball")
    hinge_gy = bpy.data.objects.get("Hinge_Green_Yellow")

    missing = [n for n, o in [
        ("Cube_Green",         green),
        ("Cube_Yellow",        yellow),
        ("Ball",               ball),
        ("Hinge_Green_Yellow", hinge_gy),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    # --- 5B: Reset hinge ---
    if hinge_gy.animation_data:
        hinge_gy.animation_data_clear()
    bpy.context.scene.frame_set(F_START)
    hinge_gy.rotation_euler = (0, 0, 0)

    # --- 5C: Parent Green to Hinge_Green_Yellow ---
    if green.parent != hinge_gy:
        parent_preserve_world(green, hinge_gy)
        print("Green parented to Hinge_Green_Yellow.")

    # --- 5D: Create Seat_Green (ball rest position inside Green) ---
    seat_green = bpy.data.objects.get("Seat_Green")
    if seat_green:
        bpy.data.objects.remove(seat_green, do_unlink=True)
    seat_green = bpy.data.objects.new("Seat_Green", None)
    seat_green.empty_display_type = 'SPHERE'
    seat_green.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_green)
    seat_green_local = green.matrix_world.inverted() @ SEAT_GREEN_WORLD
    seat_green.parent = green
    seat_green.location = seat_green_local
    print("Seat_Green created inside Cube_Green.")

    # --- 5E: Create Seat_Yellow (ball rest position inside Yellow) ---
    seat_yellow = bpy.data.objects.get("Seat_Yellow")
    if seat_yellow:
        bpy.data.objects.remove(seat_yellow, do_unlink=True)
    seat_yellow = bpy.data.objects.new("Seat_Yellow", None)
    seat_yellow.empty_display_type = 'SPHERE'
    seat_yellow.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_yellow)
    seat_yellow_local = yellow.matrix_world.inverted() @ SEAT_YELLOW_WORLD
    seat_yellow.parent = yellow
    seat_yellow.location = seat_yellow_local
    print("Seat_Yellow created inside Cube_Yellow.")

    # --- 5F: Ball COPY_TRANSFORMS constraints ---
    # Clear all existing constraints on ball first for clean state
    ball.constraints.clear()

    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name = "Latch_Green"
    latch_green.target = seat_green
    print("Latch_Green created.")

    latch_yellow = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_yellow.name = "Latch_Yellow"
    latch_yellow.target = seat_yellow
    print("Latch_Yellow created.")

    # --- 5G: Position ball at Seat_Green at frame F_START ---
    bpy.context.scene.frame_set(F_START)
    latch_green.influence  = 1.0
    latch_yellow.influence = 0.0

    # --- 5H: Keyframe hinge rotation X-axis ---
    # 0° → 90° → 180° hold → 180° → 90° → 0°
    key_rot_x(hinge_gy, F_START, 0)
    key_rot_x(hinge_gy, F_MID,   90)
    key_rot_x(hinge_gy, F_HOLD,  180)
    key_rot_x(hinge_gy, F_SWAP,  180)
    key_rot_x(hinge_gy, F_RET,   90)
    key_rot_x(hinge_gy, F_END,   0)
    print("Hinge_Green_Yellow rotation keyed.")

    # --- 5I: Keyframe constraint influences ---
    # Before swap: Latch_Green=1.0, Latch_Yellow=0.0
    # After swap:  Latch_Green=0.0, Latch_Yellow=1.0
    key_influence(ball, "Latch_Green",  F_START, 1.0)
    key_influence(ball, "Latch_Yellow", F_START, 0.0)
    key_influence(ball, "Latch_Green",  F_HOLD,  1.0)
    key_influence(ball, "Latch_Yellow", F_HOLD,  0.0)
    key_influence(ball, "Latch_Green",  F_SWAP,  0.0)
    key_influence(ball, "Latch_Yellow", F_SWAP,  1.0)
    key_influence(ball, "Latch_Green",  F_END,   0.0)
    key_influence(ball, "Latch_Yellow", F_END,   1.0)
    print("Ball influences keyed.")

    # --- 5J: Set frame range ---
    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C16 Complete: Green → Yellow ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_SWAP}")
    print("WARNING: Set hinge keys to LINEAR and influence keys to CONSTANT")
    print("         manually in Graph Editor — same as C12/C13.")
    return True

################################################################################
# SECTION 6: Blender UI Panel and Operator
################################################################################
class LORQB_PT_C16Panel(bpy.types.Panel):
    bl_label       = "LorQB C16: Green → Yellow"
    bl_idname      = "LORQB_PT_c16_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        self.layout.operator("lorqb.green_to_yellow", text="Run C16: Green → Yellow")

class LORQB_OT_GreenToYellow(bpy.types.Operator):
    bl_idname  = "lorqb.green_to_yellow"
    bl_label   = "Green to Yellow C16"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = setup_green_to_yellow()
        if success:
            self.report({'INFO'}, "C16 complete: Green → Yellow")
        else:
            self.report({'ERROR'}, "C16 failed — check console")
        return {'FINISHED'}

################################################################################
# SECTION 7: Register
################################################################################
def register():
    bpy.utils.register_class(LORQB_PT_C16Panel)
    bpy.utils.register_class(LORQB_OT_GreenToYellow)

def unregister():
    bpy.utils.unregister_class(LORQB_PT_C16Panel)
    bpy.utils.unregister_class(LORQB_OT_GreenToYellow)

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
    print("\n=== LorQB C16 Panel Ready ===")
    print("3D View → N-panel → LorQB → 'Run C16: Green → Yellow'")
