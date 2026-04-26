# ============================================================================
# C12_blue_to_red_REV.py  (Blender 5.0.1)
# C12_REV — Red → Blue
# Hinge: Hinge_Blue_Red (X-axis)
# Mirror of C13_red_to_green_REV.py — source/destination swapped
# ============================================================================

import bpy
import math
import mathutils

F_START    = 1
F_MID      = 60
F_HOLD     = 120
F_SWAP     = 121
F_RET      = 180
F_END      = 240

ROT_AXIS   = 0          # X
ROT_SIGN   = -1.0       # inverse of forward C12 (+1.0)

SEAT_RED_LOCAL  = mathutils.Vector((0.51, 0.0, -0.5))
SEAT_BLUE_WORLD = mathutils.Vector((0.51, 0.51, 0.25))


def reset_scene_to_canonical():
    all_names = ["Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]
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
            hinge.rotation_mode = 'XYZ'
            hinge.rotation_euler = (0.0, 0.0, 0.0)
    # Tear down any stale parenting from prior runs so each Run starts clean.
    for name in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
                 "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj and obj.parent is not None:
            mw = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = mw
    for seat_name in ["Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)
    bpy.context.view_layer.update()


def set_last_keyframe_interpolation(obj, data_path, frame, interp='LINEAR'):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    fcurves = None
    try:
        fcurves = action.fcurves
    except AttributeError:
        pass
    if fcurves is None:
        try:
            fcurves = action.layers[0].strips[0].channelbag_for_slot(action.slots[0]).fcurves
        except Exception:
            pass
    if fcurves is None:
        try:
            fcurves = action.layers[0].strips[0].channelbags[0].fcurves
        except Exception:
            return
    for fc in fcurves:
        if fc.data_path == data_path or data_path in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp


def key_rot(obj, frame, degrees):
    bpy.context.scene.frame_set(frame)
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=frame)
    set_last_keyframe_interpolation(obj, "rotation_euler", frame, 'LINEAR')


def key_influence(obj, constraint_name, frame, value):
    bpy.context.scene.frame_set(frame)
    con = obj.constraints.get(constraint_name)
    if not con:
        return
    con.influence = value
    data_path = f'constraints["{constraint_name}"].influence'
    obj.keyframe_insert(data_path=data_path, frame=frame)
    set_last_keyframe_interpolation(obj, data_path, frame, 'CONSTANT')


def parent_preserve_world(child, new_parent):
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw


def setup_red_to_blue():
    print("=== C12_REV Start: Red → Blue ===")
    reset_scene_to_canonical()

    blue   = bpy.data.objects.get("Cube_Blue")
    red    = bpy.data.objects.get("Cube_Red")
    green  = bpy.data.objects.get("Cube_Green")
    yellow = bpy.data.objects.get("Cube_Yellow")
    ball   = bpy.data.objects.get("Ball")
    hinge  = bpy.data.objects.get("Hinge_Blue_Red")
    hrg    = bpy.data.objects.get("Hinge_Red_Green")
    hgy    = bpy.data.objects.get("Hinge_Green_Yellow")
    missing = [n for n, o in [("Cube_Blue", blue), ("Cube_Red", red),
                              ("Cube_Green", green), ("Cube_Yellow", yellow),
                              ("Ball", ball), ("Hinge_Blue_Red", hinge),
                              ("Hinge_Red_Green", hrg),
                              ("Hinge_Green_Yellow", hgy)] if o is None]
    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    bpy.context.scene.frame_set(F_START)
    hinge.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # Sub-tree: Red rides HBR, Green rides Red via HRG (rigid weld).
    # Yellow stays on base; HGY articulates open as Green leaves.
    if red.parent != hinge:
        parent_preserve_world(red, hinge)
    if hrg.parent != red:
        parent_preserve_world(hrg, red)
    if green.parent != hrg:
        parent_preserve_world(green, hrg)
    print("Chain: HBR ← Red ← HRG ← Green   (HGY+Yellow on base)")

    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            try:
                ball.rigid_body.kinematic = True
            except Exception:
                pass

    bpy.context.view_layer.update()
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()

    seat_red_world = red.matrix_world @ SEAT_RED_LOCAL
    seat_red = bpy.data.objects.new("Seat_Red", None)
    seat_red.empty_display_type = 'SPHERE'
    seat_red.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_red)
    seat_red.parent = red
    seat_red.location = SEAT_RED_LOCAL.copy()

    ball.matrix_world.translation = seat_red_world.copy()
    bpy.context.view_layer.update()

    seat_blue_local = blue.matrix_world.inverted() @ SEAT_BLUE_WORLD
    seat_blue = bpy.data.objects.new("Seat_Blue", None)
    seat_blue.empty_display_type = 'SPHERE'
    seat_blue.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue)
    seat_blue.parent = blue
    seat_blue.location = seat_blue_local

    bpy.context.view_layer.update()

    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name = "Latch_Red"
    latch_red.target = seat_red

    latch_blue = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_blue.name = "Latch_Blue"
    latch_blue.target = seat_blue

    key_rot(hinge, F_START,   0)
    key_rot(hinge, F_MID,    90)
    key_rot(hinge, F_HOLD,  180)
    key_rot(hinge, F_SWAP,  180)
    key_rot(hinge, F_RET,    90)
    key_rot(hinge, F_END,     0)

    key_influence(ball, "Latch_Red",  F_START, 1.0)
    key_influence(ball, "Latch_Blue", F_START, 0.0)
    key_influence(ball, "Latch_Red",  F_HOLD,  1.0)
    key_influence(ball, "Latch_Blue", F_HOLD,  0.0)
    key_influence(ball, "Latch_Red",  F_SWAP,  0.0)
    key_influence(ball, "Latch_Blue", F_SWAP,  1.0)
    key_influence(ball, "Latch_Red",  F_END,   0.0)
    key_influence(ball, "Latch_Blue", F_END,   1.0)

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)
    print("=== C12_REV Complete: Red → Blue ===")
    return True


class LORQB_OT_ResetC12Rev(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c12_rev"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        reset_scene_to_canonical()
        return {'FINISHED'}


class LORQB_OT_RedToBlue(bpy.types.Operator):
    bl_idname  = "lorqb.red_to_blue"
    bl_label   = "Red to Blue C12_REV"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        ok = setup_red_to_blue()
        self.report({'INFO' if ok else 'ERROR'},
                    "C12_REV complete" if ok else "C12_REV failed")
        return {'FINISHED'}


class LORQB_PT_C12RevPanel(bpy.types.Panel):
    bl_label       = "LorQB C12_REV: Red → Blue"
    bl_idname      = "LORQB_PT_c12_rev_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'
    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c12_rev", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.red_to_blue", text="Run C12_REV: Red → Blue", icon='PLAY')


_classes = (LORQB_OT_ResetC12Rev, LORQB_OT_RedToBlue, LORQB_PT_C12RevPanel)

def register():
    for cls in _classes:
        try: bpy.utils.unregister_class(cls)
        except Exception: pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        try: bpy.utils.unregister_class(cls)
        except Exception: pass

if __name__ == "__main__":
    register()
