import bpy
import math

################################################################################
# SECTION 1: Animation Function - Green → Yellow with matrix_parent_inverse fix
# FIXED: Now uses same direct parenting approach as C12 (matrix_parent_inverse)
################################################################################

def animate_green_to_yellow():
    """Animate ball from Green to Yellow with proper parent inverse matrices"""

    # Get objects
    ball       = bpy.data.objects.get("Ball")
    green_cube = bpy.data.objects.get("Cube_Green")
    yellow_cube = bpy.data.objects.get("Cube_Yellow")
    hinge      = bpy.data.objects.get("Hinge_Green_Yellow")

    if not all([ball, green_cube, yellow_cube, hinge]):
        print("ERROR: Missing required objects")
        return

    # Clear existing animation data
    for obj in [ball, hinge, green_cube]:
        if obj.animation_data:
            obj.animation_data_clear()

    # -------------------------------------------------------------------------
    # SETUP FRAME 1: Parent with matrix_parent_inverse fix
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(1)

    # Parent Green cube to hinge (WITH matrix_parent_inverse to stay in place)
    green_cube.parent = hinge
    green_cube.parent_type = 'OBJECT'
    green_cube.matrix_parent_inverse = hinge.matrix_world.inverted()

    # Parent ball to Green cube (NO matrix_parent_inverse - ball stays inside cube)
    ball.parent = green_cube
    ball.parent_type = 'OBJECT'

    # Keyframe: Hinge at 0°
    hinge.rotation_euler[0] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=1)

    # -------------------------------------------------------------------------
    # FRAME 60: Rotate to 90°
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(60)
    hinge.rotation_euler[0] = math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=60)

    # -------------------------------------------------------------------------
    # FRAME 120: Rotate to 180° (holes align, Green on top of Yellow)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(120)
    hinge.rotation_euler[0] = math.radians(180)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=120)

    # -------------------------------------------------------------------------
    # FRAME 121: Ball transfers from Green to Yellow (NO matrix_parent_inverse)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(121)
    ball.parent = yellow_cube
    ball.parent_type = 'OBJECT'

    # -------------------------------------------------------------------------
    # FRAME 180: Return to 90°
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(180)
    hinge.rotation_euler[0] = math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=180)

    # -------------------------------------------------------------------------
    # FRAME 240: Return to 0° (Green back to flat)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(240)
    hinge.rotation_euler[0] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=240)

    # Reset to frame 1
    bpy.context.scene.frame_set(1)

    print("=== Green → Yellow FIXED ===")
    print("f1(0°) → f60(90°) → f120(180°) → f121(transfer) → f180(90°) → f240(0°)")
    print("matrix_parent_inverse applied ONLY to cube (ball stays inside)")

################################################################################
# SECTION 2: Panel and Operator
################################################################################

class LORQB_PT_AnimationPanel(bpy.types.Panel):
    bl_label = "LorQB Animation"
    bl_idname = "LORQB_PT_animation_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.green_to_yellow", text="Green → Yellow (FIXED)")

class LORQB_OT_GreenToYellow(bpy.types.Operator):
    bl_idname = "lorqb.green_to_yellow"
    bl_label = "Green to Yellow"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        animate_green_to_yellow()
        self.report({'INFO'}, "Green → Yellow animation complete (FIXED)")
        return {'FINISHED'}

################################################################################
# SECTION 3: Register Panel and Operator
################################################################################

def register():
    bpy.utils.register_class(LORQB_PT_AnimationPanel)
    bpy.utils.register_class(LORQB_OT_GreenToYellow)

def unregister():
    bpy.utils.unregister_class(LORQB_PT_AnimationPanel)
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
