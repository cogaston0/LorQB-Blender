import bpy
import math

################################################################################
# SECTION 1: Animation Function - Yellow to Blue with matrix_parent_inverse fix
# Trio consensus: Add matrix_parent_inverse ONLY for cube (not ball)
# Ball inherits cube transform directly to stay inside
################################################################################

def animate_yellow_to_blue():
    """Animate ball from Yellow to Blue with proper parent inverse matrices"""

    # Get objects
    ball         = bpy.data.objects.get("Ball")
    yellow_cube  = bpy.data.objects.get("Cube_Yellow")
    blue_cube    = bpy.data.objects.get("Cube_Blue")
    hinge        = bpy.data.objects.get("Hinge_Blue_Yellow")

    if not all([ball, yellow_cube, blue_cube, hinge]):
        print("ERROR: Missing required objects")
        return

    # Clear existing animation data
    for obj in [ball, hinge, yellow_cube]:
        if obj.animation_data:
            obj.animation_data_clear()

    # -------------------------------------------------------------------------
    # SETUP FRAME 721: Parent with matrix_parent_inverse fix
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(721)

    # Parent Yellow cube to hinge (WITH matrix_parent_inverse to stay in place)
    yellow_cube.parent = hinge
    yellow_cube.parent_type = 'OBJECT'
    yellow_cube.matrix_parent_inverse = hinge.matrix_world.inverted()

    # Parent ball to Yellow cube (NO matrix_parent_inverse - ball stays inside cube)
    ball.parent = yellow_cube
    ball.parent_type = 'OBJECT'

    # Keyframe: Hinge at 0 degrees
    hinge.rotation_euler[0] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=721)

    # -------------------------------------------------------------------------
    # FRAME 780: Rotate to 90 degrees
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(780)
    hinge.rotation_euler[0] = math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=780)

    # -------------------------------------------------------------------------
    # FRAME 840: Rotate to 180 degrees (holes align, Yellow on top of Blue)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(840)
    hinge.rotation_euler[0] = math.radians(180)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=840)

    # -------------------------------------------------------------------------
    # FRAME 841: Ball transfers from Yellow to Blue (NO matrix_parent_inverse)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(841)
    ball.parent = blue_cube
    ball.parent_type = 'OBJECT'

    # -------------------------------------------------------------------------
    # FRAME 900: Return to 90 degrees
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(900)
    hinge.rotation_euler[0] = math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=900)

    # -------------------------------------------------------------------------
    # FRAME 960: Return to 0 degrees (Yellow back to flat)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(960)
    hinge.rotation_euler[0] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=960)

    # Reset to frame 721
    bpy.context.scene.frame_set(721)

    print("=== Yellow -> Blue FIXED ===")
    print("f721(0) -> f780(90) -> f840(180) -> f841(transfer) -> f900(90) -> f960(0)")
    print("matrix_parent_inverse applied ONLY to cube (ball stays inside)")

################################################################################
# SECTION 2: Panel and Operator
################################################################################

class LORQB_PT_C15Panel(bpy.types.Panel):
    bl_label       = "LorQB C15: Yellow -> Blue"
    bl_idname      = "LORQB_PT_c15_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        self.layout.operator("lorqb.yellow_to_blue", text="Yellow -> Blue (FIXED)")

class LORQB_OT_YellowToBlue(bpy.types.Operator):
    bl_idname  = "lorqb.yellow_to_blue"
    bl_label   = "Yellow to Blue"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        animate_yellow_to_blue()
        self.report({'INFO'}, "Yellow -> Blue animation complete (FIXED)")
        return {'FINISHED'}

################################################################################
# SECTION 3: Register Panel and Operator
################################################################################

def register():
    bpy.utils.register_class(LORQB_PT_C15Panel)
    bpy.utils.register_class(LORQB_OT_YellowToBlue)

def unregister():
    bpy.utils.unregister_class(LORQB_PT_C15Panel)
    bpy.utils.unregister_class(LORQB_OT_YellowToBlue)

################################################################################
# SECTION 4: Main Execution
################################################################################

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
    print("\n=== LorQB Yellow -> Blue Panel Ready (FIXED) ===")
    print("3D View > N-panel > LorQB > Click 'Yellow -> Blue (FIXED)'")
