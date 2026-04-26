# ============================================================================
# C13_green_to_red.py  (Blender 5.0.1)
# C13_REV — Green → Red
# Hinge: Hinge_Red_Green (Y-axis)
# Mirror of C13_red_to_green.py — source/destination swapped, ROT_SIGN inverted
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

ROT_AXIS   = 1          # Y
ROT_SIGN   = +1.0       # inverse of forward C13 (-1.0)

SEAT_GREEN_LOCAL = mathutils.Vector((0.0, -0.51, -0.5))
SEAT_RED_WORLD   = mathutils.Vector((0.51, -0.51, 0.5))


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


def setup_green_to_red():
    print("=== C13_REV Start: Green → Red ===")
    reset_scene_to_canonical()

    green = bpy.data.objects.get("Cube_Green")
    red   = bpy.data.objects.get("Cube_Red")
    yellow = bpy.data.objects.get("Cube_Yellow")
    ball   = bpy.data.objects.get("Ball")
    hinge  = bpy.data.objects.get("Hinge_Red_Green")
    hgy    = bpy.data.objects.get("Hinge_Green_Yellow")
    missing = [n for n, o in [("Cube_Green", green), ("Cube_Red", red),
                              ("Cube_Yellow", yellow), ("Ball", ball),
                              ("Hinge_Red_Green", hinge),
                              ("Hinge_Green_Yellow", hgy)] if o is None]
    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    bpy.context.scene.frame_set(F_START)
    hinge.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # Sub-tree: Green rides HRG, Yellow rides Green via HGY (rigid weld).
    if green.parent != hinge:
        parent_preserve_world(green, hinge)
    if hgy.parent != green:
        parent_preserve_world(hgy, green)
    if yellow.parent != hgy:
        parent_preserve_world(yellow, hgy)
    print("Chain: HRG ← Green ← HGY ← Yellow   (Red+Blue on base)")

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

    seat_green_world = green.matrix_world @ SEAT_GREEN_LOCAL
    seat_green = bpy.data.objects.new("Seat_Green", None)
    seat_green.empty_display_type = 'SPHERE'
    seat_green.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_green)
    seat_green.parent = green
    seat_green.location = SEAT_GREEN_LOCAL.copy()

    ball.matrix_world.translation = seat_green_world.copy()
    bpy.context.view_layer.update()

    seat_red_local = red.matrix_world.inverted() @ SEAT_RED_WORLD
    seat_red = bpy.data.objects.new("Seat_Red", None)
    seat_red.empty_display_type = 'SPHERE'
    seat_red.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_red)
    seat_red.parent = red
    seat_red.location = seat_red_local

    bpy.context.view_layer.update()

    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name = "Latch_Green"
    latch_green.target = seat_green

    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name = "Latch_Red"
    latch_red.target = seat_red

    key_rot(hinge, F_START,   0)
    key_rot(hinge, F_MID,    90)
    key_rot(hinge, F_HOLD,  180)
    key_rot(hinge, F_SWAP,  180)
    key_rot(hinge, F_RET,    90)
    key_rot(hinge, F_END,     0)

    key_influence(ball, "Latch_Green", F_START, 1.0)
    key_influence(ball, "Latch_Red",   F_START, 0.0)
    key_influence(ball, "Latch_Green", F_HOLD,  1.0)
    key_influence(ball, "Latch_Red",   F_HOLD,  0.0)
    key_influence(ball, "Latch_Green", F_SWAP,  0.0)
    key_influence(ball, "Latch_Red",   F_SWAP,  1.0)
    key_influence(ball, "Latch_Green", F_END,   0.0)
    key_influence(ball, "Latch_Red",   F_END,   1.0)

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)
    print("=== C13_REV Complete: Green → Red ===")
    return True


class LORQB_OT_ResetC13Rev(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c13_rev"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        reset_scene_to_canonical()
        return {'FINISHED'}


class LORQB_OT_GreenToRed(bpy.types.Operator):
    bl_idname  = "lorqb.green_to_red"
    bl_label   = "Green to Red C13_REV"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        ok = setup_green_to_red()
        self.report({'INFO' if ok else 'ERROR'},
                    "C13_REV complete" if ok else "C13_REV failed")
        return {'FINISHED'}


class LORQB_PT_C13RevPanel(bpy.types.Panel):
    bl_label       = "LorQB C13_REV: Green → Red"
    bl_idname      = "LORQB_PT_c13_rev_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'
    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c13_rev", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.green_to_red", text="Run C13_REV: Green → Red", icon='PLAY')


_classes = (LORQB_OT_ResetC13Rev, LORQB_OT_GreenToRed, LORQB_PT_C13RevPanel)

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
