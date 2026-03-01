import bpy
import math

################################################################################
# SECTION 1: Animation Function - Green → Yellow with matrix_parent_inverse fix
# Trio consensus: Add matrix_parent_inverse ONLY for cube (not ball)
# Ball inherits cube transform directly to stay inside
################################################################################

def animate_green_to_yellow():
    """Animate ball from Green to Yellow with proper parent inverse matrices"""

    # Get objects
    ball         = bpy.data.objects.get("Ball")
    green_cube   = bpy.data.objects.get("Cube_Green")
    yellow_cube  = bpy.data.objects.get("Cube_Yellow")
    hinge        = bpy.data.objects.get("Hinge_Green_Yellow")

    if not all([ball, green_cube, yellow_cube, hinge]):
        print("ERROR: Missing required objects")
        return

    # Clear existing animation data
    for obj in [ball, hinge, green_cube]:
        if obj.animation_data:
            obj.animation_data_clear()

    # -------------------------------------------------------------------------
    # SETUP FRAME 481: Parent with matrix_parent_inverse fix
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(481)

    # Parent Green cube to hinge (WITH matrix_parent_inverse to stay in place)
    green_cube.parent = hinge
    green_cube.parent_type = 'OBJECT'
    green_cube.matrix_parent_inverse = hinge.matrix_world.inverted()

    # Parent ball to Green cube (NO matrix_parent_inverse - ball stays inside cube)
    ball.parent = green_cube
    ball.parent_type = 'OBJECT'

    # Keyframe: Hinge at 0°
    hinge.rotation_euler[0] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=481)

    # -------------------------------------------------------------------------
    # FRAME 540: Rotate to 90°
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(540)
    hinge.rotation_euler[0] = math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=540)

    # -------------------------------------------------------------------------
    # FRAME 600: Rotate to 180° (holes align, Green on top of Yellow)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(600)
    hinge.rotation_euler[0] = math.radians(180)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=600)

    # -------------------------------------------------------------------------
    # FRAME 601: Ball transfers from Green to Yellow (NO matrix_parent_inverse)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(601)
    ball.parent = yellow_cube
    ball.parent_type = 'OBJECT'

    # -------------------------------------------------------------------------
    # FRAME 660: Return to 90°
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(660)
    hinge.rotation_euler[0] = math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=660)

    # -------------------------------------------------------------------------
    # FRAME 720: Return to 0° (Green back to flat)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(720)
    hinge.rotation_euler[0] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=720)

    # Reset to frame 481
    bpy.context.scene.frame_set(481)

    print("=== Green → Yellow FIXED ===")
    print("f481(0°) → f540(90°) → f600(180°) → f601(transfer) → f660(90°) → f720(0°)")
    print("matrix_parent_inverse applied ONLY to cube (ball stays inside)")

################################################################################
# SECTION 2: Panel and Operator
################################################################################

class LORQB_PT_C14Panel(bpy.types.Panel):
    bl_label       = "LorQB C14: Green → Yellow"
    bl_idname      = "LORQB_PT_c14_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        self.layout.operator("lorqb.green_to_yellow", text="Green → Yellow (FIXED)")

class LORQB_OT_GreenToYellow(bpy.types.Operator):
    bl_idname  = "lorqb.green_to_yellow"
    bl_label   = "Green to Yellow"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        animate_green_to_yellow()
        self.report({'INFO'}, "Green → Yellow animation complete (FIXED)")
        return {'FINISHED'}

################################################################################
# SECTION 3: Register Panel and Operator
################################################################################

def register():
    bpy.utils.register_class(LORQB_PT_C14Panel)
    bpy.utils.register_class(LORQB_OT_GreenToYellow)

def unregister():
    bpy.utils.unregister_class(LORQB_PT_C14Panel)
    bpy.utils.unregister_class(LORQB_OT_GreenToYellow)

################################################################################
# SECTION 4: Main Execution
################################################################################

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
    print("\n=== LorQB Green → Yellow Panel Ready (FIXED) ===")
    print("3D View > N-panel > LorQB > Click 'Green → Yellow (FIXED)'")
