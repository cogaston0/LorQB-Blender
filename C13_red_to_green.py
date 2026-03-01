import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
# Chain: Blue — Red — Green — Yellow
# C13: Ball transfers from Red to Green
# Red rotates 180° around Hinge_Red_Green (bottom edge, Y-axis)
# Blue parented to Red — passively swings above Yellow at 180°
# Frame range: 241 — 480
# NOTE: Interpolation (LINEAR/CONSTANT) must be set manually in Graph Editor
#       after running this script — same approach as C12.
################################################################################
F_START = 241   # Start: Red at 0°, ball in Red
F_MID   = 300   # Mid:   Red at 90°
F_HOLD  = 360   # Hold:  Red at 180° — ball aligned above Green
F_SWAP  = 361   # Swap:  ball transfers from Seat_Red to Seat_Green
F_RET   = 420   # Return: Red at 90° on way back
F_END   = 480   # End:   Red at 0°, ball in Green

ROT_AXIS = 1        # Y-axis index in rotation_euler
ROT_SIGN = 1.0      # Positive Y rotation swings Red correctly over Green

SEAT_RED_WORLD   = mathutils.Vector((0.51,  -0.51, 0.25))
SEAT_GREEN_WORLD = mathutils.Vector((-0.51, -0.51, 0.25))

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
# SECTION 3: Helper — key Y-axis rotation
################################################################################
def key_rot_y(obj, frame, degrees):
    """Insert Y-axis rotation keyframe."""
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
# SECTION 5: Main C13 setup function
################################################################################
def setup_red_to_green():

    # --- 5A: Validate required objects ---
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

    # --- 5B: Reset hinge ---
    if hinge_rg.animation_data:
        hinge_rg.animation_data_clear()
    bpy.context.scene.frame_set(F_START)
    hinge_rg.rotation_euler = (0, 0, 0)

    # --- 5C: Parent Blue to Red (passive carry) ---
    if blue.parent != red:
        parent_preserve_world(blue, red)
        print("Blue parented to Red — passive carry.")

    # --- 5D: Parent Red to Hinge_Red_Green ---
    if red.parent != hinge_rg:
        parent_preserve_world(red, hinge_rg)
        print("Red parented to Hinge_Red_Green.")

    # --- 5E: Create Seat_Red (ball rest position inside Red) ---
    # Created here so C13 works standalone without depending on C12
    seat_red = bpy.data.objects.get("Seat_Red")
    if seat_red:
        bpy.data.objects.remove(seat_red, do_unlink=True)
    seat_red = bpy.data.objects.new("Seat_Red", None)
    seat_red.empty_display_type = 'SPHERE'
    seat_red.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_red)
    seat_red_local = red.matrix_world.inverted() @ SEAT_RED_WORLD
    seat_red.parent = red
    seat_red.location = seat_red_local
    print("Seat_Red created inside Cube_Red.")

    # --- 5F: Create Seat_Green (ball rest position inside Green) ---
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

    # --- 5G: Ball COPY_TRANSFORMS constraints ---
    # Clear all existing constraints on ball first for clean state
    ball.constraints.clear()

    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name = "Latch_Red"
    latch_red.target = seat_red
    print("Latch_Red created.")

    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name = "Latch_Green"
    latch_green.target = seat_green
    print("Latch_Green created.")

    # --- 5H: Position ball at Seat_Red at frame F_START ---
    bpy.context.scene.frame_set(F_START)
    latch_red.influence   = 1.0
    latch_green.influence = 0.0

    # --- 5I: Keyframe hinge rotation Y-axis ---
    # 0° → 90° → 180° hold → 180° → 90° → 0°
    key_rot_y(hinge_rg, F_START, 0)
    key_rot_y(hinge_rg, F_MID,   90)
    key_rot_y(hinge_rg, F_HOLD,  180)
    key_rot_y(hinge_rg, F_SWAP,  180)
    key_rot_y(hinge_rg, F_RET,   90)
    key_rot_y(hinge_rg, F_END,   0)
    print("Hinge_Red_Green rotation keyed.")

    # --- 5J: Keyframe constraint influences ---
    # Before swap: Latch_Red=1.0, Latch_Green=0.0
    # After swap:  Latch_Red=0.0, Latch_Green=1.0
    key_influence(ball, "Latch_Red",   F_START, 1.0)
    key_influence(ball, "Latch_Green", F_START, 0.0)
    key_influence(ball, "Latch_Red",   F_HOLD,  1.0)
    key_influence(ball, "Latch_Green", F_HOLD,  0.0)
    key_influence(ball, "Latch_Red",   F_SWAP,  0.0)
    key_influence(ball, "Latch_Green", F_SWAP,  1.0)
    key_influence(ball, "Latch_Red",   F_END,   0.0)
    key_influence(ball, "Latch_Green", F_END,   1.0)
    print("Ball influences keyed.")

    # --- 5K: Set frame range ---
    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C13 Complete: Red → Green ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_SWAP}")
    print(f"Blue above Yellow at frame {F_HOLD}")
    print("WARNING: Set hinge keys to LINEAR and influence keys to CONSTANT")
    print("         manually in Graph Editor — same as C12.")
    return True

################################################################################
# SECTION 6: Blender UI Panel and Operator
################################################################################
class LORQB_PT_C13Panel(bpy.types.Panel):
    bl_label       = "LorQB C13: Red → Green"
    bl_idname      = "LORQB_PT_c13_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        self.layout.operator("lorqb.red_to_green", text="Run C13: Red → Green")

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
# SECTION 7: Register
################################################################################
def register():
    bpy.utils.register_class(LORQB_PT_C13Panel)
    bpy.utils.register_class(LORQB_OT_RedToGreen)

def unregister():
    bpy.utils.unregister_class(LORQB_PT_C13Panel)
    bpy.utils.unregister_class(LORQB_OT_RedToGreen)

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
    print("\n=== LorQB C13 Panel Ready ===")
    print("3D View → N-panel → LorQB → 'Run C13: Red → Green'")
