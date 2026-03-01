import bpy
import math

################################################################################
# SECTION 1: Constants
# Chain: Blue — Red — Green — Yellow
# C13: Ball transfers from Red to Green
# Red rotates 180° around Hinge_Red_Green (bottom edge, Y-axis)
# Blue parented to Red — passively swings above Yellow at 180°
# Frame range: 241 — 480
# FIXED: Now uses same direct parenting approach as C12 (matrix_parent_inverse)
################################################################################
F_START = 241   # Start: Red at 0°, ball in Red
F_MID   = 300   # Mid:   Red at 90°
F_HOLD  = 360   # Hold:  Red at 180° — ball aligned above Green
F_SWAP  = 361   # Swap:  ball transfers from Red to Green
F_RET   = 420   # Return: Red at 90° on way back
F_END   = 480   # End:   Red at 0°, ball in Green

ROT_AXIS = 1        # Y-axis index in rotation_euler
ROT_SIGN = 1.0      # Positive Y rotation swings Red correctly over Green

################################################################################
# SECTION 2: Helper — key Y-axis rotation
################################################################################
def key_rot_y(obj, frame, degrees):
    """Insert Y-axis rotation keyframe."""
    bpy.context.scene.frame_set(frame)
    obj.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=frame)

################################################################################
# SECTION 3: Main C13 setup function
################################################################################
def setup_red_to_green():
    """Animate ball from Red to Green with consistent direct parenting approach"""

    # --- 3A: Validate required objects ---
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

    # --- 3B: Clear existing animation data ---
    for obj in [ball, hinge_rg, red, blue]:
        if obj and obj.animation_data:
            obj.animation_data_clear()

    # Clear any constraints on ball
    if ball.constraints:
        ball.constraints.clear()

    # --- 3C: SETUP FRAME F_START: Parent with matrix_parent_inverse fix ---
    bpy.context.scene.frame_set(F_START)
    hinge_rg.rotation_euler = (0, 0, 0)

    # Parent Red cube to hinge (WITH matrix_parent_inverse to stay in place)
    red.parent = hinge_rg
    red.parent_type = 'OBJECT'
    red.matrix_parent_inverse = hinge_rg.matrix_world.inverted()

    # Parent Blue to Red (passive carry WITH matrix_parent_inverse)
    blue.parent = red
    blue.parent_type = 'OBJECT'
    blue.matrix_parent_inverse = red.matrix_world.inverted()

    # Parent ball to Red cube (NO matrix_parent_inverse - ball stays inside cube)
    ball.parent = red
    ball.parent_type = 'OBJECT'
    print("Red parented to Hinge_Red_Green with matrix_parent_inverse.")
    print("Blue parented to Red (passive carry) with matrix_parent_inverse.")
    print("Ball parented to Red without matrix_parent_inverse.")

    # --- 3D: Keyframe hinge rotation Y-axis ---
    # 0° → 90° → 180° hold → 180° → 90° → 0°
    key_rot_y(hinge_rg, F_START, 0)
    key_rot_y(hinge_rg, F_MID,   90)
    key_rot_y(hinge_rg, F_HOLD,  180)
    key_rot_y(hinge_rg, F_SWAP,  180)
    key_rot_y(hinge_rg, F_RET,   90)
    key_rot_y(hinge_rg, F_END,   0)
    print("Hinge_Red_Green rotation keyed.")

    # --- 3E: FRAME F_SWAP: Ball transfers from Red to Green ---
    bpy.context.scene.frame_set(F_SWAP)
    ball.parent = green
    ball.parent_type = 'OBJECT'
    print(f"Ball transferred to Green at frame {F_SWAP}.")

    # --- 3F: Set frame range ---
    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C13 Complete: Red → Green (FIXED) ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_SWAP}")
    print(f"Blue above Yellow at frame {F_HOLD}")
    print("matrix_parent_inverse applied ONLY to cubes (ball stays inside)")
    return True

################################################################################
# SECTION 4: Blender UI Panel and Operator
################################################################################
class LORQB_PT_C13Panel(bpy.types.Panel):
    bl_label       = "LorQB C13: Red → Green"
    bl_idname      = "LORQB_PT_c13_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        self.layout.operator("lorqb.red_to_green", text="Run C13: Red → Green (FIXED)")

class LORQB_OT_RedToGreen(bpy.types.Operator):
    bl_idname  = "lorqb.red_to_green"
    bl_label   = "Red to Green C13"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = setup_red_to_green()
        if success:
            self.report({'INFO'}, "C13 complete: Red → Green (FIXED)")
        else:
            self.report({'ERROR'}, "C13 failed — check console")
        return {'FINISHED'}

################################################################################
# SECTION 5: Register
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
    print("\n=== LorQB C13 Panel Ready (FIXED) ===")
    print("3D View → N-panel → LorQB → 'Run C13: Red → Green (FIXED)'")
