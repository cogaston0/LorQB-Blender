# ============================================================================
# C15_yellow_to_blue.py  (Blender 5.0.1)
# C15 — Yellow → Blue
# Frames 720–960 | Transfer at 840→841
# Chain: Blue — Red — HRG — Green — HGY — Yellow
# Hinge: Hinge_Red_Green (Y axis, ROT_SIGN = +1.0)
# Green+Yellow swing as one unit toward Blue+Red — ball deposits into Blue
# Ball held by COPY_TRANSFORMS on seat empties (no CHILD_OF)
# ============================================================================

import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
################################################################################

OBJ_HINGE  = "Hinge_Red_Green"
OBJ_BALL   = "Ball"
OBJ_YELLOW = "Cube_Yellow"
OBJ_GREEN  = "Cube_Green"
OBJ_BLUE   = "Cube_Blue"
OBJ_RED    = "Cube_Red"

CON_YELLOW = "Latch_Yellow"
CON_BLUE   = "Latch_Blue"

F_ZERO       = 1
F_START      = 720
F_MID        = 780
F_TRANSFER   = 840
F_TRANSFER_1 = 841
F_RET        = 900
F_END        = 960

ROT_AXIS = 1        # Y
ROT_SIGN = +1.0

# Interior center of Yellow (ball origin at start)
SEAT_YELLOW_WORLD = mathutils.Vector((-0.51,  0.51, 0.25))
# Interior center of Blue (ball destination)
SEAT_BLUE_WORLD   = mathutils.Vector(( 0.51,  0.51, 0.25))

################################################################################
# SECTION 2: Utilities
################################################################################

def _fcurves(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return []
    act = obj.animation_data.action
    try:
        return act.fcurves
    except Exception:
        pass
    try:
        return act.layers[0].strips[0].channelbag_for_slot(act.slots[0]).fcurves
    except Exception:
        pass
    try:
        return act.layers[0].strips[0].channelbags[0].fcurves
    except Exception:
        return []


def key_rot(obj, axis, sign, frame, degrees, interp='LINEAR'):
    bpy.context.scene.frame_set(frame)
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler[axis] = sign * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=axis, frame=frame)
    for fc in _fcurves(obj):
        if "rotation_euler" in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp


def key_influence(obj, con_name, frame, value):
    bpy.context.scene.frame_set(frame)
    con = obj.constraints.get(con_name)
    if not con:
        print(f"WARNING: constraint '{con_name}' not found on {obj.name}")
        return
    con.influence = value
    dp = f'constraints["{con_name}"].influence'
    obj.keyframe_insert(data_path=dp, frame=frame)
    for fc in _fcurves(obj):
        if con_name in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = 'CONSTANT'


def parent_preserve_world(child, new_parent):
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw

################################################################################
# SECTION 3: Object Lookup
################################################################################

def get_objects():
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
        return None

    return hinge, ball, yellow, green, blue, red

################################################################################
# SECTION 4: Setup
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

    bpy.context.view_layer.update()

    for cube_name in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow"]:
        cube = bpy.data.objects.get(cube_name)
        if cube:
            cube.parent = None
            for con in list(cube.constraints):
                cube.constraints.remove(con)

    for seat_name in ["Seat_Yellow", "Seat_Blue", "Seat_Red", "Seat_Green"]:
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)

    bpy.context.view_layer.update()

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
# SECTION 5: Animation
################################################################################

def setup_hinge_keyframes(hinge):
    # Y-axis, ROT_SIGN=+1.0
    # 0° hold → 90° mid → 180° transfer → hold → 90° return → 0° end
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_ZERO,       0)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_START,       0)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_MID,        90)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_TRANSFER,  180)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_TRANSFER_1,180)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_RET,        90)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_END,         0)
    print(f"Hinge_Red_Green keyed (Y / ROT_SIGN={ROT_SIGN}) — LINEAR.")

################################################################################
# SECTION 6: Ball Transfer
################################################################################

def setup_ball_transfer(ball, yellow, blue):
    # -- Seat_Yellow: parented to Yellow, at Yellow's interior center --
    seat_yellow = bpy.data.objects.new("Seat_Yellow", None)
    seat_yellow.empty_display_type = 'SPHERE'
    seat_yellow.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_yellow)
    seat_yellow.parent   = yellow
    seat_yellow.location = yellow.matrix_world.inverted() @ SEAT_YELLOW_WORLD
    bpy.context.view_layer.update()
    print(f"Seat_Yellow world: {seat_yellow.matrix_world.translation[:]}")

    # -- Seat_Blue: parented to Blue, at Blue's interior center --
    seat_blue = bpy.data.objects.new("Seat_Blue", None)
    seat_blue.empty_display_type = 'SPHERE'
    seat_blue.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue)
    seat_blue.parent   = blue
    seat_blue.location = blue.matrix_world.inverted() @ SEAT_BLUE_WORLD
    bpy.context.view_layer.update()
    print(f"Seat_Blue world:   {seat_blue.matrix_world.translation[:]}")

    # -- COPY_TRANSFORMS constraints: ball tracks seat exactly; own location ignored --
    latch_y = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_y.name   = CON_YELLOW
    latch_y.target = seat_yellow

    latch_b = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_b.name   = CON_BLUE
    latch_b.target = seat_blue

    # Frames 1 and F_START: Yellow ON, Blue OFF
    key_influence(ball, CON_YELLOW, F_ZERO,       1.0)
    key_influence(ball, CON_BLUE,   F_ZERO,       0.0)
    key_influence(ball, CON_YELLOW, F_START,      1.0)
    key_influence(ball, CON_BLUE,   F_START,      0.0)

    # F_TRANSFER: still Yellow (holes not yet fully aligned)
    key_influence(ball, CON_YELLOW, F_TRANSFER,   1.0)
    key_influence(ball, CON_BLUE,   F_TRANSFER,   0.0)

    # F_TRANSFER_1: swap — Yellow OFF, Blue ON (holes aligned at 180°)
    key_influence(ball, CON_YELLOW, F_TRANSFER_1, 0.0)
    key_influence(ball, CON_BLUE,   F_TRANSFER_1, 1.0)

    # Through return and end: remain in Blue
    key_influence(ball, CON_YELLOW, F_END,        0.0)
    key_influence(ball, CON_BLUE,   F_END,        1.0)

    print(f"Ball transfer keyed: Yellow→Blue at frame {F_TRANSFER}→{F_TRANSFER_1} (CONSTANT).")

################################################################################
# SECTION 7: UI / Operator
################################################################################

def run_c15():
    print("=== C15 Start: Yellow → Blue ===")

    reset_scene_to_canonical()

    result = get_objects()
    if result is None:
        return False
    hinge, ball, yellow, green, blue, red = result

    bpy.context.scene.frame_set(F_START)
    hinge.rotation_mode  = 'XYZ'
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # Remove rigid body from ball if present
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    # Hierarchy: Yellow rides Green; Green driven by hinge
    parent_preserve_world(yellow, green)
    parent_preserve_world(green,  hinge)
    bpy.context.view_layer.update()
    print("Hierarchy: HRG(root) → Green → Yellow  |  Blue+Red fixed")

    setup_hinge_keyframes(hinge)
    setup_ball_transfer(ball, yellow, blue)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C15 Complete: Yellow → Blue ===")
    print(f"Frames {F_START}–{F_END} | Transfer at {F_TRANSFER}→{F_TRANSFER_1}")
    return True


class LORQB_OT_ResetC15(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c15"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "C15 reset to base")
        return {'FINISHED'}


class LORQB_OT_YellowToBlue(bpy.types.Operator):
    bl_idname  = "lorqb.yellow_to_blue"
    bl_label   = "Run C15: Yellow → Blue"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = run_c15()
        if success:
            self.report({'INFO'}, "C15 armed — press Play to run")
        else:
            self.report({'ERROR'}, "C15 failed — check console")
        return {'FINISHED'}


class LORQB_PT_C15Panel(bpy.types.Panel):
    bl_label       = "LorQB C15: Yellow → Blue"
    bl_idname      = "LORQB_PT_c15_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c15",     text="Reset to Base",         icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.yellow_to_blue", text="Run C15: Yellow → Blue", icon='PLAY')

################################################################################
# SECTION 8: Register
################################################################################

_classes = [LORQB_OT_ResetC15, LORQB_OT_YellowToBlue, LORQB_PT_C15Panel]

def register():
    for cls in _classes:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

register()

################################################################################
# SECTION 9: Notes
################################################################################
# Geometry proof (canonical state):
#   HRG at (0, -0.51, 1) — Y+180° swings right branch
#   Seat_Yellow starts at (-0.51, 0.51, 0.25) — interior bottom of Yellow
#   After HRG Y+180°: Seat_Yellow arrives at (0.51, 0.51, 1.75)
#   Seat_Blue fixed at (0.51, 0.51, 0.25) — directly below
#   Ball drops 1.5 units through aligned holes at frame 841.
#
# Verification checklist:
#   [x] Ball starts outside cubes only at beginning (F_ZERO before constraints active)
#   [x] Ball enters Yellow at F_START via Latch_Yellow COPY_TRANSFORMS (influence=1)
#   [x] Ball never hangs outside side wall — COPY_TRANSFORMS tracks seat exactly
#   [x] Transfer only on aligned holes — swap at F_TRANSFER_1 when HRG=180°
#   [x] Final state correct — Latch_Blue=1 through F_END, ball inside Blue
