# ============================================================================
# lorqb_yellow_to_blue_C15.py
# Blender 5.0.1
# C15 — Yellow -> Blue
# Frames 720–960 | Transfer at 840→841
# INDEPENDENT: Places ball inside Yellow at frame 720 regardless of prior state
# Chain: Blue — Red — Green — Yellow
# Hinge: Hinge_Red_Green (bottom edge — X axis rotation)
# Green+Yellow swing as one unit — Blue+Red stay fixed on world base
# All movement via CHILD_OF constraints — NO direct parenting
# FIX: SEAT_YELLOW_WORLD and SEAT_BLUE_WORLD Z corrected to 0.25 (cube center)
# FIX: Green and Yellow forced to canonical positions before Set Inverse
# FIX: animation_data_clear on Green and Yellow in 6F to prevent C14 key override
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
CON_G_HINGE = "C15_Hinge"
CON_Y_GREEN = "C15_Carry"

F_ZERO       = 1
F_START      = 720
F_MID        = 780
F_TRANSFER   = 840
F_TRANSFER_1 = 841
F_RET        = 900
F_END        = 960

# Hinge_Red_Green is on the BOTTOM edge — X axis rotation
ROT_AXIS = 0
ROT_SIGN = +1.0

# Seat world positions — Z=0.25 is cube center
SEAT_YELLOW_WORLD = mathutils.Vector((-0.51,  0.51, 0.25))
SEAT_BLUE_WORLD   = mathutils.Vector(( 0.51,  0.51, 0.25))

# Canonical cube positions in the 2x2 grid
CANONICAL_GREEN  = mathutils.Vector((-0.51, -0.51, 0.25))
CANONICAL_YELLOW = mathutils.Vector((-0.51,  0.51, 0.25))

################################################################################
# SECTION 2: Helper — force CONSTANT interpolation
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
# SECTION 3: Helper — force LINEAR interpolation
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
# SECTION 4: Helper — ensure CHILD_OF constraint exists
################################################################################
def ensure_child_of(obj, name, target):
    con = obj.constraints.get(name)
    if not con:
        con = obj.constraints.new(type='CHILD_OF')
        con.name = name
    con.target = target
    return con

################################################################################
# SECTION 5: Helper — set inverse via operator (guaranteed no jump)
################################################################################
def set_inverse_via_operator(obj, constraint_name):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.context.view_layer.update()
    bpy.ops.constraint.childof_set_inverse(
        constraint=constraint_name,
        owner='OBJECT'
    )
    bpy.context.view_layer.update()
    print(f"Set Inverse applied: {obj.name} / {constraint_name}")

################################################################################
# SECTION 6: Main C15 setup function
################################################################################
def setup_yellow_to_blue():
    print("=== C15 Start: Yellow → Blue ===")

    # --- 6A: Validate required objects ---
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

    # --- 6B: Go to start frame ---
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()

    # --- 6C: Reset hinge animation ---
    if hinge.animation_data:
        hinge.animation_data_clear()
    hinge.rotation_mode = "XYZ"
    hinge.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # --- 6D: Clear prior constraints on Green and Yellow ---
    for obj in [green, yellow]:
        for con in list(obj.constraints):
            obj.constraints.remove(con)
    print("Prior constraints cleared on Green and Yellow.")

    # --- 6E: Clear prior constraints on Ball ---
    ball.constraints.clear()
    print("Prior constraints cleared on Ball.")

    # --- 6F: Clear prior parents AND animation data on Green and Yellow ---
    for obj in [green, yellow]:
        if obj.parent:
            mw = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = mw
    # Clear animation data so C14 keyed locations do not override canonical positions
    for obj in [green, yellow]:
        if obj.animation_data:
            obj.animation_data_clear()
    bpy.context.view_layer.update()
    print("Prior parents and animation data cleared on Green and Yellow.")

    # --- 6G: Force canonical positions before Set Inverse ---
    green.location        = CANONICAL_GREEN.copy()
    green.rotation_euler  = (0, 0, 0)
    yellow.location       = CANONICAL_YELLOW.copy()
    yellow.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    print(f"Cube_Green  forced to canonical: {green.matrix_world.translation[:]}")
    print(f"Cube_Yellow forced to canonical: {yellow.matrix_world.translation[:]}")
    print(f"Cube_Blue   actual world:        {blue.matrix_world.translation[:]}")
    print(f"Hinge       actual world:        {hinge.matrix_world.translation[:]}\n")

    # --- 6H: Green CHILD_OF Hinge_Red_Green ---
    con_g = ensure_child_of(green, CON_G_HINGE, hinge)
    con_g.influence = 1.0
    bpy.context.view_layer.update()
    set_inverse_via_operator(green, CON_G_HINGE)
    bpy.context.view_layer.update()
    print(f"Green world after Set Inverse: {green.matrix_world.translation[:]}")
    print("Green CHILD_OF Hinge_Red_Green — Set Inverse applied.")

    # --- 6I: Yellow CHILD_OF Green ---
    con_yg = ensure_child_of(yellow, CON_Y_GREEN, green)
    con_yg.influence = 1.0
    bpy.context.view_layer.update()
    set_inverse_via_operator(yellow, CON_Y_GREEN)
    bpy.context.view_layer.update()
    print(f"Yellow world after Set Inverse: {yellow.matrix_world.translation[:]}")
    print("Yellow CHILD_OF Green — Set Inverse applied.")

    # --- 6J: Create Seat_Yellow empty inside Yellow ---
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
    bpy.context.view_layer.update()
    print(f"Seat_Yellow local:        {seat_yellow_local[:]}")
    print(f"Seat_Yellow world actual: {seat_yellow.matrix_world.translation[:]}")
    print("Seat_Yellow created inside Cube_Yellow.")

    # --- 6K: Create Seat_Blue empty inside Blue ---
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
    bpy.context.view_layer.update()
    print(f"Seat_Blue local:        {seat_blue_local[:]}")
    print(f"Seat_Blue world actual: {seat_blue.matrix_world.translation[:]}")
    print("Seat_Blue created inside Cube_Blue.")

    # --- 6L: Setup ball CHILD_OF constraints ---
    con_y = ensure_child_of(ball, CON_YELLOW, seat_yellow)
    con_b = ensure_child_of(ball, CON_BLUE,   seat_blue)

    # --- 6M: Place ball at Yellow seat world position ---
    ball.location = SEAT_YELLOW_WORLD.copy()
    bpy.context.view_layer.update()

    # =========================================================================
    # Key ALL C15 constraints at frame 1 with influence=0 — scrub-safe
    # =========================================================================
    bpy.context.scene.frame_set(F_ZERO)
    bpy.context.view_layer.update()

    con_g.influence = 0.0
    con_g.keyframe_insert(data_path="influence", frame=F_ZERO)
    force_constant(green, f'constraints["{CON_G_HINGE}"].influence')

    con_yg.influence = 0.0
    con_yg.keyframe_insert(data_path="influence", frame=F_ZERO)
    force_constant(yellow, f'constraints["{CON_Y_GREEN}"].influence')

    con_y.influence = 0.0
    con_y.keyframe_insert(data_path="influence", frame=F_ZERO)

    con_b.influence = 0.0
    con_b.keyframe_insert(data_path="influence", frame=F_ZERO)

    print(f"All C15 constraints zeroed at frame {F_ZERO}.")

    # Raise influences to operational state at F_START
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()

    con_g.influence = 1.0
    con_g.keyframe_insert(data_path="influence", frame=F_START)
    force_constant(green, f'constraints["{CON_G_HINGE}"].influence')

    con_yg.influence = 1.0
    con_yg.keyframe_insert(data_path="influence", frame=F_START)
    force_constant(yellow, f'constraints["{CON_Y_GREEN}"].influence')

    print(f"Green C15_Hinge and Yellow C15_Carry raised to 1.0 at frame {F_START}.")

    # --- 6N: Frame F_START — ball locked to Yellow ---
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()
    con_y.influence = 1.0
    con_b.influence = 0.0
    set_inverse_via_operator(ball, CON_YELLOW)
    bpy.context.view_layer.update()
    print(f"Ball world after lock to Yellow: {ball.matrix_world.translation[:]}\n")
    con_y.keyframe_insert(data_path="influence", frame=F_START)
    con_b.keyframe_insert(data_path="influence", frame=F_START)
    print(f"Ball locked to Seat_Yellow at frame {F_START}.")

    # --- 6O: Keyframe hinge rotation — X-axis LINEAR ---
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
    print("Hinge_Red_Green rotation keyed (X-axis) — LINEAR.")

    # Key hinge at F_ZERO to prevent drift before F_START
    hinge.rotation_euler[ROT_AXIS] = 0.0
    hinge.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=F_ZERO)
    force_linear(hinge, "rotation_euler")
    print(f"Hinge rotation zeroed at frame {F_ZERO}.")

    # --- 6P: Frame F_TRANSFER — capture Blue inverse BEFORE switch ---
    bpy.context.scene.frame_set(F_TRANSFER)
    bpy.context.view_layer.update()
    con_b.influence = 1.0
    bpy.context.view_layer.update()
    set_inverse_via_operator(ball, CON_BLUE)
    con_b.influence = 0.0
    bpy.context.view_layer.update()
    print(f"Ball world at transfer frame:    {ball.matrix_world.translation[:]}")
    print(f"Blue inverse_matrix captured via Set Inverse at frame {F_TRANSFER}.")

    # --- 6Q: Frame F_TRANSFER_1 — switch ball to Blue ---
    bpy.context.scene.frame_set(F_TRANSFER_1)
    con_y.influence = 0.0
    con_b.influence = 1.0
    con_y.keyframe_insert(data_path="influence", frame=F_TRANSFER_1)
    con_b.keyframe_insert(data_path="influence", frame=F_TRANSFER_1)
    print(f"Ball switched to Seat_Blue at frame {F_TRANSFER_1}.")

    # --- 6R: Frame F_END — maintain Blue ownership ---
    con_y.keyframe_insert(data_path="influence", frame=F_END)
    con_b.keyframe_insert(data_path="influence", frame=F_END)
    print(f"Ball remains in Seat_Blue through frame {F_END}.")

    # Zero out C15_Hinge and C15_Carry at F_END
    con_g.influence = 0.0
    con_g.keyframe_insert(data_path="influence", frame=F_END)
    force_constant(green, f'constraints["{CON_G_HINGE}"].influence')

    con_yg.influence = 0.0
    con_yg.keyframe_insert(data_path="influence", frame=F_END)
    force_constant(yellow, f'constraints["{CON_Y_GREEN}"].influence')

    print(f"Green C15_Hinge and Yellow C15_Carry zeroed at frame {F_END}.")

    # --- 6S: Force CONSTANT interpolation on all ball influences ---
    force_constant(ball, f'constraints["{CON_YELLOW}"].influence')
    force_constant(ball, f'constraints["{CON_BLUE}"].influence')
    print("Ball influences forced CONSTANT.")

    # --- 6T: Set frame range ---
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C15 Complete: Yellow → Blue ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_TRANSFER}→{F_TRANSFER_1}")
    print(f"Hinge: {OBJ_HINGE} | Axis: X | ROT_SIGN: {ROT_SIGN}")
    print(f"SEAT_YELLOW_WORLD: {SEAT_YELLOW_WORLD[:]}")
    print(f"SEAT_BLUE_WORLD:   {SEAT_BLUE_WORLD[:]}")
    print("Green+Yellow swung as one unit over Red+Blue.")
    print("Blue+Red stayed fixed on world base.")
    print(f"All constraints zeroed at frame {F_ZERO} and frame {F_END} — scrub-safe.")
    return True

################################################################################
# SECTION 7: Blender UI Panel and Operator
################################################################################
class LORQB_PT_C15Panel(bpy.types.Panel):
    bl_label       = "LorQB C15: Yellow → Blue"
    bl_idname      = "LORQB_PT_c15_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.yellow_to_blue", text="Run C15: Yellow → Blue", icon="CONSTRAINT")
        col = layout.column(align=True)
        col.label(text="Transfer: Frame 840 → 841 @ 180°")
        col.label(text="Green+Yellow swing over — Blue+Red stay fixed")

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
# SECTION 8: Register / Unregister
################################################################################
def register():
    for cls in [LORQB_PT_C15Panel, LORQB_OT_YellowToBlue]:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in [LORQB_OT_YellowToBlue, LORQB_PT_C15Panel]:
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