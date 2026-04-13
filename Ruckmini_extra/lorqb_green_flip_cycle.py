import bpy

################################################################################
# SECTION 1: Animation Function
################################################################################
def animate_green_flip_cycle():
    """Animate Green cube flip cycle: 0° → 90° → 180° → 90° → 0° (240 frames)"""
    
    # Get objects
    ball = bpy.data.objects.get("Ball")
    green_cube = bpy.data.objects.get("Cube_Green")
    yellow_cube = bpy.data.objects.get("Cube_Yellow")
    hinge_green_yellow = bpy.data.objects.get("Hinge_Green_Yellow")
    
    if not all([ball, green_cube, yellow_cube, hinge_green_yellow]):
        print("ERROR: Missing required objects")
        return
    
    # Clear existing animation data
    if ball.animation_data:
        ball.animation_data_clear()
    if hinge_green_yellow.animation_data:
        hinge_green_yellow.animation_data_clear()
    
    # Frame 1: Rotation = 0°, Ball parent to Green
    bpy.context.scene.frame_set(1)
    ball.parent = green_cube
    hinge_green_yellow.rotation_euler[0] = 0
    hinge_green_yellow.keyframe_insert(data_path="rotation_euler", index=0, frame=1)
    
    # Frame 60: Rotation = 90° (1.5708 radians)
    bpy.context.scene.frame_set(60)
    hinge_green_yellow.rotation_euler[0] = 1.5708
    hinge_green_yellow.keyframe_insert(data_path="rotation_euler", index=0, frame=60)
    
    # Frame 120: Rotation = 180° (3.14159 radians), Ball transfer to Yellow
    bpy.context.scene.frame_set(120)
    hinge_green_yellow.rotation_euler[0] = 3.14159
    hinge_green_yellow.keyframe_insert(data_path="rotation_euler", index=0, frame=120)
    
    # Clear parent and set ball to Yellow cube's bottom-center position
    ball.parent = None
    
    # Calculate Yellow cube's bottom-center position
    yellow_dims = yellow_cube.dimensions
    yellow_loc = yellow_cube.location
    ball_radius = 0.25
    
    ball.location = (
        yellow_loc.x,
        yellow_loc.y,
        yellow_loc.z - (yellow_dims.z / 2) + ball_radius * 0.99
    )
    
    # Now parent to Yellow
    ball.parent = yellow_cube
    
    # Frame 180: Rotation = 90° (1.5708 radians)
    bpy.context.scene.frame_set(180)
    hinge_green_yellow.rotation_euler[0] = 1.5708
    hinge_green_yellow.keyframe_insert(data_path="rotation_euler", index=0, frame=180)
    
    # Frame 240: Rotation = 0° (back to base)
    bpy.context.scene.frame_set(240)
    hinge_green_yellow.rotation_euler[0] = 0
    hinge_green_yellow.keyframe_insert(data_path="rotation_euler", index=0, frame=240)
    
    # Reset to frame 1
    bpy.context.scene.frame_set(1)
    
    print("=== Green Flip Cycle Complete ===")
    print("Keyframes: f1(0°), f60(90°), f120(180°), f180(90°), f240(0°)")
    print("Ball transfers to Yellow at frame 120")

################################################################################
# SECTION 2: Create 3D Viewport Button Panel
################################################################################
class LORQB_PT_AnimationPanel(bpy.types.Panel):
    """Creates a Panel in the 3D View N-panel"""
    bl_label = "LorQB Animation"
    bl_idname = "LORQB_PT_animation_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LorQB'
    
    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.green_flip_cycle", text="Green Flip Cycle")

class LORQB_OT_GreenFlipCycle(bpy.types.Operator):
    """Animate Green cube flip cycle with ball transfer"""
    bl_idname = "lorqb.green_flip_cycle"
    bl_label = "Green Flip Cycle"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        animate_green_flip_cycle()
        self.report({'INFO'}, "Green Flip Cycle: 240 frames created")
        return {'FINISHED'}

################################################################################
# SECTION 3: Register Panel and Operator
################################################################################
def register():
    bpy.utils.register_class(LORQB_PT_AnimationPanel)
    bpy.utils.register_class(LORQB_OT_GreenFlipCycle)

def unregister():
    bpy.utils.unregister_class(LORQB_PT_AnimationPanel)
    bpy.utils.unregister_class(LORQB_OT_GreenFlipCycle)

# Run registration
if __name__ == "__main__":
    # Unregister first to avoid duplicate registration errors
    try:
        unregister()
    except:
        pass
    
    register()
    print("\n=== LorQB Animation Panel Added ===")
    print("Open 3D View > N-panel > LorQB tab > Click 'Green Flip Cycle' button")
