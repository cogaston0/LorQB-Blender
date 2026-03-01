import bpy
import math

################################################################################
# SECTION 1: Animation Function - Red → Green with matrix_parent_inverse fix
# Trio consensus: Add matrix_parent_inverse ONLY for cube (not ball)
# Ball inherits cube transform directly to stay inside
################################################################################

def animate_red_to_green():
    """Animate ball from Red to Green with proper parent inverse matrices"""

    # Get objects
    ball       = bpy.data.objects.get("Ball")
    red_cube   = bpy.data.objects.get("Cube_Red")
    green_cube = bpy.data.objects.get("Cube_Green")
    hinge      = bpy.data.objects.get("Hinge_Red_Green")

    if not all([ball, red_cube, green_cube, hinge]):
        print("ERROR: Missing required objects")
        return

    # Clear existing animation data
    for obj in [ball, hinge, red_cube]:
        if obj.animation_data:
            obj.animation_data_clear()

    # -------------------------------------------------------------------------
    # SETUP FRAME 241: Parent with matrix_parent_inverse fix
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(241)

    # Parent Red cube to hinge (WITH matrix_parent_inverse to stay in place)
    red_cube.parent = hinge
    red_cube.parent_type = 'OBJECT'
    red_cube.matrix_parent_inverse = hinge.matrix_world.inverted()

    # Parent ball to Red cube (NO matrix_parent_inverse - ball stays inside cube)
    ball.parent = red_cube
    ball.parent_type = 'OBJECT'

    # Keyframe: Hinge at 0°
    hinge.rotation_euler[0] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=241)

    # -------------------------------------------------------------------------
    # FRAME 300: Rotate to 90°
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(300)
    hinge.rotation_euler[0] = math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=300)

    # -------------------------------------------------------------------------
    # FRAME 360: Rotate to 180° (holes align, Red on top of Green)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(360)
    hinge.rotation_euler[0] = math.radians(180)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=360)

    # -------------------------------------------------------------------------
    # FRAME 361: Ball transfers from Red to Green (NO matrix_parent_inverse)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(361)
    ball.parent = green_cube
    ball.parent_type = 'OBJECT'

    # -------------------------------------------------------------------------
    # FRAME 420: Return to 90°
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(420)
    hinge.rotation_euler[0] = math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=420)

    # -------------------------------------------------------------------------
    # FRAME 480: Return to 0° (Red back to flat)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(480)
    hinge.rotation_euler[0] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=480)

    # Reset to frame 241
    bpy.context.scene.frame_set(241)

    print("=== Red → Green FIXED ===")
    print("f241(0°) → f300(90°) → f360(180°) → f361(transfer) → f420(90°) → f480(0°)")
    print("matrix_parent_inverse applied ONLY to cube (ball stays inside)")

################################################################################
# SECTION 2: Panel and Operator
################################################################################

class LORQB_PT_C13Panel(bpy.types.Panel):
    bl_label       = "LorQB C13: Red → Green"
    bl_idname      = "LORQB_PT_c13_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        self.layout.operator("lorqb.red_to_green", text="Red → Green (FIXED)")

class LORQB_OT_RedToGreen(bpy.types.Operator):
    bl_idname  = "lorqb.red_to_green"
    bl_label   = "Red to Green"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        animate_red_to_green()
        self.report({'INFO'}, "Red → Green animation complete (FIXED)")
        return {'FINISHED'}

################################################################################
# SECTION 3: Register Panel and Operator
################################################################################

def register():
    bpy.utils.register_class(LORQB_PT_C13Panel)
    bpy.utils.register_class(LORQB_OT_RedToGreen)

def unregister():
    bpy.utils.unregister_class(LORQB_PT_C13Panel)
    bpy.utils.unregister_class(LORQB_OT_RedToGreen)

################################################################################
# SECTION 4: Main Execution
################################################################################

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
    print("\n=== LorQB Red → Green Panel Ready (FIXED) ===")
    print("3D View > N-panel > LorQB > Click 'Red → Green (FIXED)'")
