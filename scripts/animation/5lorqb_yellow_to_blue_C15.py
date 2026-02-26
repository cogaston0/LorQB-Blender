# ============================================================================
# 5lorqb_yellow_to_blue_C15.py  (Blender 5.0.1)
# ----------------------------------------------------------------------------
# LorQB Level 1 - Sequence C15 (Yellow -> Blue)
# Hinge: Hinge_Yellow_Blue  (top edge, (0, 0.51, 1))
# Axis: Y
#
# Ball transfers from Yellow to Blue.
# Yellow rotates 180 degrees around Hinge_Yellow_Blue (top edge, Y-axis).
# Green parented to Yellow -- passively carries along.
# Frame range: 721 - 960
# NOTE: Interpolation (LINEAR/CONSTANT) must be set manually in Graph Editor
#       after running this script -- same approach as C12/C13/C14.
# ============================================================================

import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
################################################################################
F_START = 721   # Start: Yellow at 0 deg, ball in Yellow
F_MID   = 780   # Mid:   Yellow at 90 deg
F_HOLD  = 840   # Hold:  Yellow at 180 deg -- ball aligned above Blue
F_SWAP  = 841   # Swap:  ball transfers from Seat_Yellow to Seat_Blue
F_RET   = 900   # Return: Yellow at 90 deg on way back
F_END   = 960   # End:   Yellow at 0 deg, ball in Blue

ROT_AXIS = 1        # Y-axis index in rotation_euler
ROT_SIGN = 1.0      # Positive Y rotation swings Yellow correctly over Blue

SEAT_YELLOW_WORLD = mathutils.Vector((-0.51,  0.51, 0.25))
SEAT_BLUE_WORLD   = mathutils.Vector(( 0.51,  0.51, 0.25))

################################################################################
# SECTION 2: Helper -- parent preserving world transform
################################################################################
def parent_preserve_world(child, new_parent):
    """Parent child to new_parent while keeping child's world transform."""
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw

################################################################################
# SECTION 3: Helper -- key Y-axis rotation
################################################################################
def key_rot_y(obj, frame, degrees):
    """Insert Y-axis rotation keyframe."""
    bpy.context.scene.frame_set(frame)
    obj.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=frame)

################################################################################
# SECTION 4: Helper -- key constraint influence
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
# SECTION 5: Main C15 setup function
################################################################################
def setup_yellow_to_blue():

    # --- 5A: Validate required objects ---
    yellow   = bpy.data.objects.get("Cube_Yellow")
    blue     = bpy.data.objects.get("Cube_Blue")
    green    = bpy.data.objects.get("Cube_Green")
    ball     = bpy.data.objects.get("Ball")
    hinge_yb = bpy.data.objects.get("Hinge_Yellow_Blue")

    missing = [n for n, o in [
        ("Cube_Yellow",      yellow),
        ("Cube_Blue",        blue),
        ("Cube_Green",       green),
        ("Ball",             ball),
        ("Hinge_Yellow_Blue", hinge_yb),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    # --- 5B: Reset hinge ---
    if hinge_yb.animation_data:
        hinge_yb.animation_data_clear()
    bpy.context.scene.frame_set(F_START)
    hinge_yb.rotation_euler = (0, 0, 0)

    # --- 5C: Parent Green to Yellow (passive carry) ---
    if green.parent != yellow:
        parent_preserve_world(green, yellow)
        print("Green parented to Yellow -- passive carry.")

    # --- 5D: Parent Yellow to Hinge_Yellow_Blue ---
    if yellow.parent != hinge_yb:
        parent_preserve_world(yellow, hinge_yb)
        print("Yellow parented to Hinge_Yellow_Blue.")

    # --- 5E: Create Seat_Yellow (ball rest position inside Yellow) ---
    # Created here so C15 works standalone without depending on C14
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

    # --- 5F: Create Seat_Blue (ball rest position inside Blue) ---
    seat_blue = bpy.data.objects.get("Seat_Blue")
    if seat_blue:
        bpy.data.objects.remove(seat_blue, do_unlink=True)
    seat_blue = bpy.data.objects.new("Seat_Blue", None)
    seat_blue.empty_display_type = 'SPHERE'
    seat_blue.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue)
    seat_blue_local = blue.matrix_world.inverted() @ SEAT_BLUE_WORLD
    seat_blue.parent = blue
    seat_blue.location = seat_blue_local
    print("Seat_Blue created inside Cube_Blue.")

    # --- 5G: Ball COPY_TRANSFORMS constraints ---
    # Clear all existing constraints on ball first for clean state
    ball.constraints.clear()

    latch_yellow = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_yellow.name = "Latch_Yellow"
    latch_yellow.target = seat_yellow
    print("Latch_Yellow created.")

    latch_blue = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_blue.name = "Latch_Blue"
    latch_blue.target = seat_blue
    print("Latch_Blue created.")

    # --- 5H: Position ball at Seat_Yellow at frame F_START ---
    bpy.context.scene.frame_set(F_START)
    latch_yellow.influence = 1.0
    latch_blue.influence   = 0.0

    # --- 5I: Keyframe hinge rotation Y-axis ---
    # 0 deg -> 90 deg -> 180 deg hold -> 180 deg -> 90 deg -> 0 deg
    key_rot_y(hinge_yb, F_START, 0)
    key_rot_y(hinge_yb, F_MID,   90)
    key_rot_y(hinge_yb, F_HOLD,  180)
    key_rot_y(hinge_yb, F_SWAP,  180)
    key_rot_y(hinge_yb, F_RET,   90)
    key_rot_y(hinge_yb, F_END,   0)
    print("Hinge_Yellow_Blue rotation keyed.")

    # --- 5J: Keyframe constraint influences ---
    # Before swap: Latch_Yellow=1.0, Latch_Blue=0.0
    # After swap:  Latch_Yellow=0.0, Latch_Blue=1.0
    key_influence(ball, "Latch_Yellow", F_START, 1.0)
    key_influence(ball, "Latch_Blue",   F_START, 0.0)
    key_influence(ball, "Latch_Yellow", F_HOLD,  1.0)
    key_influence(ball, "Latch_Blue",   F_HOLD,  0.0)
    key_influence(ball, "Latch_Yellow", F_SWAP,  0.0)
    key_influence(ball, "Latch_Blue",   F_SWAP,  1.0)
    key_influence(ball, "Latch_Yellow", F_END,   0.0)
    key_influence(ball, "Latch_Blue",   F_END,   1.0)
    print("Ball influences keyed.")

    # --- 5K: Set frame range ---
    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C15 Complete: Yellow -> Blue ===")
    print(f"Frames {F_START}-{F_END} | Transfer at frame {F_SWAP}")
    print(f"Green above Blue at frame {F_HOLD}")
    print("WARNING: Set hinge keys to LINEAR and influence keys to CONSTANT")
    print("         manually in Graph Editor -- same as C12/C13/C14.")
    return True

################################################################################
# SECTION 6: Blender UI Panel and Operator
################################################################################
class LORQB_PT_C15Panel(bpy.types.Panel):
    bl_label       = "LorQB C15: Yellow -> Blue"
    bl_idname      = "LORQB_PT_c15_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        self.layout.operator("lorqb.yellow_to_blue", text="Run C15: Yellow -> Blue")

class LORQB_OT_YellowToBlue(bpy.types.Operator):
    bl_idname  = "lorqb.yellow_to_blue"
    bl_label   = "Yellow to Blue C15"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = setup_yellow_to_blue()
        if success:
            self.report({'INFO'}, "C15 complete: Yellow -> Blue")
        else:
            self.report({'ERROR'}, "C15 failed -- check console")
        return {'FINISHED'}

################################################################################
# SECTION 7: Register
################################################################################
def register():
    bpy.utils.register_class(LORQB_PT_C15Panel)
    bpy.utils.register_class(LORQB_OT_YellowToBlue)

def unregister():
    bpy.utils.unregister_class(LORQB_PT_C15Panel)
    bpy.utils.unregister_class(LORQB_OT_YellowToBlue)

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
    print("\n=== LorQB C15 Panel Ready ===")
    print("3D View -> N-panel -> LorQB -> 'Run C15: Yellow -> Blue'")
