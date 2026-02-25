import bpy
import math

################################################################################
# SECTION 1: Animation Function - Blue → Red with matrix_parent_inverse fix
# Trio consensus: Add matrix_parent_inverse ONLY for cube (not ball)
# Ball inherits cube transform directly to stay inside
################################################################################

def animate_blue_to_red():
    """Animate ball from Blue to Red with proper parent inverse matrices"""
    
    # Get objects
    ball       = bpy.data.objects.get("Ball")
    blue_cube  = bpy.data.objects.get("Cube_Blue")
    red_cube   = bpy.data.objects.get("Cube_Red")
    hinge      = bpy.data.objects.get("Hinge_Red_Blue")
    
    if not all([ball, blue_cube, red_cube, hinge]):
        print("ERROR: Missing required objects")
        return
    
    # Clear existing animation data
    for obj in [ball, hinge, blue_cube]:
        if obj.animation_data:
            obj.animation_data_clear()
    
    # -------------------------------------------------------------------------
    # SETUP FRAME 1: Parent with matrix_parent_inverse fix
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(1)
    
    # Parent Blue cube to hinge (WITH matrix_parent_inverse to stay in place)
    blue_cube.parent = hinge
    blue_cube.parent_type = 'OBJECT'
    blue_cube.matrix_parent_inverse = hinge.matrix_world.inverted()
    
    # Parent ball to Blue cube (NO matrix_parent_inverse - ball stays inside cube)
    ball.parent = blue_cube
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
    # FRAME 120: Rotate to 180° (holes align, Blue on top of Red)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(120)
    hinge.rotation_euler[0] = math.radians(180)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=120)
    
    # -------------------------------------------------------------------------
    # FRAME 121: Ball transfers from Blue to Red (NO matrix_parent_inverse)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(121)
    ball.parent = red_cube
    ball.parent_type = 'OBJECT'
    
    # -------------------------------------------------------------------------
    # FRAME 180: Return to 90°
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(180)
    hinge.rotation_euler[0] = math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=180)
    
    # -------------------------------------------------------------------------
    # FRAME 240: Return to 0° (Blue back to flat)
    # -------------------------------------------------------------------------
    bpy.context.scene.frame_set(240)
    hinge.rotation_euler[0] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=0, frame=240)
    
    # Reset to frame 1
    bpy.context.scene.frame_set(1)
    
    print("=== Blue → Red FIXED ===")
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
        layout.operator("lorqb.blue_to_red", text="Blue → Red (FIXED)")

class LORQB_OT_BlueToRed(bpy.types.Operator):
    bl_idname = "lorqb.blue_to_red"
    bl_label = "Blue to Red"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        animate_blue_to_red()
        self.report({'INFO'}, "Blue → Red animation complete (FIXED)")
        return {'FINISHED'}

################################################################################
# SECTION 3: Register Panel and Operator
################################################################################

def register():
    bpy.utils.register_class(LORQB_PT_AnimationPanel)
    bpy.utils.register_class(LORQB_OT_BlueToRed)

def unregister():
    bpy.utils.unregister_class(LORQB_PT_AnimationPanel)
    bpy.utils.unregister_class(LORQB_OT_BlueToRed)

################################################################################
# SECTION 4: Main Execution
################################################################################

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
    print("\n=== LorQB Blue → Red Panel Ready (FIXED) ===")
    print("3D View > N-panel > LorQB > Click 'Blue → Red (FIXED)'")
