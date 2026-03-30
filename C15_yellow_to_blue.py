# ============================================================================
# C15_yellow_to_blue.py  (Blender 5.0.1)
# C15 — Yellow -> Blue
# Frames 720–960 | Transfer at 840→841
# Chain: Blue — Red — Green — Yellow
# Hinge: Hinge_Red_Green (Y axis, ROT_SIGN = +1.0)
# Green+Yellow swing as one unit toward Blue+Red — ball deposits into Blue
# All movement via direct parenting on cubes — CHILD_OF only on Ball
# FIX: Ball placed at SEAT_BLUE_WORLD before Blue inverse capture
# ============================================================================
import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
################################################################################
OBJ_HINGE   = "Hinge_Red_Green"
OBJ_BALL    = "Ball"
OBJ_YELLOW  = "Cube_Yellow"
OBJ_GREEN   = "Cube_Green"
OBJ_BLUE    = "Cube_Blue"
OBJ_RED     = "Cube_Red"

CON_YELLOW  = "C15_Yellow"
CON_BLUE    = "C15_Blue"

F_ZERO       = 1
F_START      = 720
F_MID        = 780
F_TRANSFER   = 840
F_TRANSFER_1 = 841
F_RET        = 900
F_END        = 960

ROT_AXIS = 1
ROT_SIGN = +1.0

SEAT_YELLOW_WORLD = mathutils.Vector((-0.51,  0.51, 0.25))
SEAT_BLUE_WORLD   = mathutils.Vector(( 0.51,  0.51, 0.25))

################################################################################
# SECTION 2: RESET — Full canonical reset (matches C14 pattern exactly)
################################################################################
def reset_scene_to_canonical():
    all_names = [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
    ]

    for name in all_names:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    for hinge_name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        hinge = bpy.data.objects.get(hinge_name)
        if hinge:
            hinge.rotation_mode  = 'XYZ'
            hinge.rotation_euler = (0.0, 0.0, 0.0)

    # Flush depsgraph before clearing parents so world transforms are stable
    bpy.context.view_layer.update()

    for cube_name in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow"]:
        cube = bpy.data.objects.get(cube_name)
        if cube:
            cube.parent = None
            for con in list(cube.constraints):
                cube.constraints.remove(con)

    for seat_name in ["Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)

    bpy.context.view_layer.update()

    # Restore canonical world positions — required when coming from C14
    canonical = {
        "Cube_Blue":          ( 0.51,  0.0,  1.0),
        "Cube_Red":           ( 0.0,  -0.51, 1.0),
        "Cube_Green":         (-0.51,  0.0,  1.0),
        "Cube_Yellow":        (-0.51,  0.0,  1.0),
        "Hinge_Blue_Red":     ( 0.51,  0.0,  1.0),
        "Hinge_Red_Green":    ( 0.0,  -0.51, 1.0),
        "Hinge_Green_Yellow": (-0.51,  0.0,  1.0),
    }
    for name, loc in canonical.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location       = loc
            obj.rotation_mode  = 'XYZ'
            obj.rotation_euler = (0.0, 0.0, 0.0)

    bpy.context.view_layer.update()
    print("=== C15 reset: canonical positions restored ===")

################################################################################
# SECTION 3: Helper — force CONSTANT interpolation
################################################################################
def force_constant(obj, data_fragment):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    act = ad.action
    for layer in act.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for fc in channelbag.fcurves:
                    if data_fragment in fc.data_path:
                        for kp in fc.keyframe_points:
                            kp.interpolation = 'CONSTANT'

################################################################################
# SECTION 4: Helper — force LINEAR interpolation
################################################################################
def force_linear(obj, data_fragment):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    act = ad.action
    for layer in act.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for fc in channelbag.fcurves:
                    if data_fragment in fc.data_path:
                        for kp in fc.keyframe_points:
                            kp.interpolation = 'LINEAR'

################################################################################
# SECTION 5: Helper — ensure CHILD_OF constraint exists
################################################################################
def ensure_child_of(obj, name, target):
    con = obj.constraints.get(name)
    if not con:
        con = obj.constraints.new(type='CHILD_OF')
        con.name = name
    con.target = target
    return con

################################################################################
# SECTION 6: Helper — parent preserving world transform
################################################################################
def parent_preserve_world(child, new_parent):
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw

################################################################################
# SECTION 8: Main C15 setup function
################################################################################
def setup_yellow_to_blue():
    print("=== C15 Start: Yellow → Blue ===")

    # --- 8A: Full canonical reset ---
    reset_scene_to_canonical()

    # --- 8B: Validate required objects ---
    hinge  = bpy.data.objects.get(OBJ_HINGE)
    ball   = bpy.data.objects.get(OBJ_BALL)
    yellow = bpy.data.objects.get(OBJ_YELLOW)
    green  = bpy.data.objects.get(OBJ_GREEN)
    blue   = bpy.data.objects.get(OBJ_BLUE)
    red    = bpy.data.objects.get(OBJ_RED)

    missing = [n for n, o in [
        (OBJ_HINGE,  hinge),
        (OBJ_BALL,   ball),
        (OBJ_YELLOW, yellow),
        (OBJ_GREEN,  green),
        (OBJ_BLUE,   blue),
        (OBJ_RED,    red),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    # --- 8C: Go to start frame ---
    bpy.context.scene.frame_set(F_START)
    hinge.rotation_mode = 'XYZ'
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # --- 8D: Confirm positions after reset ---
    print(f"Cube_Green  world: {green.matrix_world.translation[:]}\n")
    print(f"Cube_Yellow world: {yellow.matrix_world.translation[:]}\n")
    print(f"Cube_Blue   world: {blue.matrix_world.translation[:]}\n")
    print(f"Cube_Red    world: {red.matrix_world.translation[:]}\n")
    print(f"Hinge       world: {hinge.matrix_world.translation[:]}\n")

    # --- 8E: Direct parenting — Yellow rides Green, Green driven by hinge ---
    parent_preserve_world(yellow, green)
    print("Yellow parented to Green — rides passively with Green.")
    parent_preserve_world(green, hinge)
    print("Green parented to Hinge_Red_Green — active arm.")
    bpy.context.view_layer.update()

    # --- 8F: Create Seat_Yellow inside Yellow ---
    seat_yellow = bpy.data.objects.new("Seat_Yellow", None)
    seat_yellow.empty_display_type = 'SPHERE'
    seat_yellow.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_yellow)
    seat_yellow_local = yellow.matrix_world.inverted() @ SEAT_YELLOW_WORLD
    seat_yellow.parent = yellow
    seat_yellow.location = seat_yellow_local
    bpy.context.view_layer.update()
    print(f"Seat_Yellow local:        {seat_yellow_local[:]}")
    print(f"Seat_Yellow world actual: {seat_yellow.matrix_world.translation[:]}\n")

    # --- 8G: Create Seat_Blue inside Blue ---
    seat_blue = bpy.data.objects.new("Seat_Blue", None)
    seat_blue.empty_display_type = 'SPHERE'
    seat_blue.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue)
    seat_blue_local = blue.matrix_world.inverted() @ SEAT_BLUE_WORLD
    seat_blue.parent = blue
    seat_blue.location = seat_blue_local
    bpy.context.view_layer.update()
    print(f"Seat_Blue local:        {seat_blue_local[:]}")
    print(f"Seat_Blue world actual: {seat_blue.matrix_world.translation[:]}\n")

    # --- 8H: Ball CHILD_OF constraints ---
    con_y = ensure_child_of(ball, CON_YELLOW, seat_yellow)
    con_b = ensure_child_of(ball, CON_BLUE,   seat_blue)

    # --- 8I: Place ball at Yellow seat ---
    ball.location = SEAT_YELLOW_WORLD.copy()
    bpy.context.view_layer.update()

    # --- 8J: Hinge rotation keyframes — Y axis LINEAR ---
    bpy.context.scene.frame_set(F_ZERO)
    hinge.rotation_euler[ROT_AXIS] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=F_ZERO)

    bpy.context.scene.frame_set(F_START)
    hinge.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(0)
    hinge.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=F_START)

    bpy.context.scene.frame_set(F_MID)
    hinge.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=F_MID)

    bpy.context.scene.frame_set(F_TRANSFER)
    hinge.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(180)
    hinge.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=F_TRANSFER)

    bpy.context.scene.frame_set(F_TRANSFER_1)
    hinge.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(180)
    hinge.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=F_TRANSFER_1)

    bpy.context.scene.frame_set(F_RET)
    hinge.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(90)
    hinge.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=F_RET)

    bpy.context.scene.frame_set(F_END)
    hinge.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(0)
    hinge.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=F_END)

    force_linear(hinge, "rotation_euler")
    print("Hinge_Red_Green rotation keyed (Y-axis, ROT_SIGN=+1.0) — LINEAR.")

    # --- 8K: Ball locked to Yellow at F_START ---
    # Identity inverse = ball tracks seat exactly, no operator needed
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()
    con_y.inverse_matrix = mathutils.Matrix.Identity(4)
    con_y.influence = 1.0
    con_b.influence = 0.0
    bpy.context.view_layer.update()
    print(f"Ball world after lock to Yellow: {ball.matrix_world.translation[:]}")
    con_y.keyframe_insert(data_path="influence", frame=F_START)
    con_b.keyframe_insert(data_path="influence", frame=F_START)
    print(f"Ball locked to Seat_Yellow at frame {F_START}.")

    # --- 8L: Set Blue inverse directly ---
    # Identity inverse = ball tracks Seat_Blue exactly at transfer, no dependency
    # on whether Seat_Yellow and Seat_Blue are precisely coincident at 180°
    con_b.inverse_matrix = mathutils.Matrix.Identity(4)
    print(f"CON_BLUE inverse set to Identity — ball will track Seat_Blue exactly.")

    # --- 8M: Switch ball to Blue at F_TRANSFER_1 ---
    bpy.context.scene.frame_set(F_TRANSFER_1)
    con_y.influence = 0.0
    con_b.influence = 1.0
    con_y.keyframe_insert(data_path="influence", frame=F_TRANSFER_1)
    con_b.keyframe_insert(data_path="influence", frame=F_TRANSFER_1)
    print(f"Ball switched to Seat_Blue at frame {F_TRANSFER_1}.")

    # --- 8N: Maintain Blue through F_END ---
    con_y.keyframe_insert(data_path="influence", frame=F_END)
    con_b.keyframe_insert(data_path="influence", frame=F_END)
    print(f"Ball remains in Seat_Blue through frame {F_END}.")

    # --- 8O: Force CONSTANT on all ball influences ---
    force_constant(ball, f'constraints["{CON_YELLOW}"].influence')
    force_constant(ball, f'constraints["{CON_BLUE}"].influence')
    print("Ball influences forced CONSTANT.")

    # --- 8P: Set frame range ---
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C15 Complete: Yellow → Blue ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_TRANSFER}→{F_TRANSFER_1}")
    print(f"Hinge: {OBJ_HINGE} | Axis: Y | ROT_SIGN: {ROT_SIGN}")
    print(f"SEAT_YELLOW_WORLD: {SEAT_YELLOW_WORLD[:]}")
    print(f"SEAT_BLUE_WORLD:   {SEAT_BLUE_WORLD[:]}")
    print("Green+Yellow swung as one unit toward Blue+Red.")
    print("Blue+Red stayed fixed on world base.")
    return True

################################################################################
# SECTION 9: Blender UI Panel and Operator
################################################################################
class LORQB_OT_ResetC15(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c15"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "Reset to base complete")
        return {'FINISHED'}

class LORQB_PT_C15Panel(bpy.types.Panel):
    bl_label       = "LorQB C15: Yellow → Blue"
    bl_idname      = "LORQB_PT_c15_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c15", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.yellow_to_blue", text="Run C15: Yellow → Blue", icon="CONSTRAINT")
        col = layout.column(align=True)
        col.label(text="Transfer: Frame 840 → 841 @ 180°")
        col.label(text="Green+Yellow swing toward Blue+Red")

class LORQB_OT_YellowToBlue(bpy.types.Operator):
    bl_idname  = "lorqb.yellow_to_blue"
    bl_label   = "Yellow to Blue C15"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = setup_yellow_to_blue()
        if success:
            self.report({'INFO'}, "C15 complete: Yellow → Blue")
        else:
            self.report({'ERROR'}, "C15 failed — check console")
        return {'FINISHED'}

################################################################################
# SECTION 10: Register / Unregister
################################################################################
def register():
    for cls in [LORQB_OT_ResetC15, LORQB_PT_C15Panel, LORQB_OT_YellowToBlue]:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in [LORQB_OT_YellowToBlue, LORQB_PT_C15Panel, LORQB_OT_ResetC15]:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

if __name__ == "__main__":
    register()
    print("\n==================================================")
    print("✓ LorQB C15 Panel Ready.")
    print("3D View → N-panel → LorQB → 'Run C15: Yellow → Blue'")
    print("==================================================\n")