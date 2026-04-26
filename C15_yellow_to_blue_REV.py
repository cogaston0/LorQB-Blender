# ============================================================================
# C15_blue_to_yellow.py  (Blender 5.0.1)
# C15_REV — Blue → Yellow
# Hinge: Hinge_Red_Green (Y-axis)  (same hinge as forward C15)
# Mirror of C15_yellow_to_blue.py — source/destination swapped, ROT_SIGN inverted
# ============================================================================

import bpy
import math
import mathutils

F_START, F_MID, F_HOLD, F_SWAP, F_RET, F_END = 1, 60, 120, 121, 180, 240

ROT_AXIS = 1          # Y
ROT_SIGN = -1.0       # inverse of forward C15 — the other side of HRG folds

# Blue rides Red as passive carrier. Blue's origin is at HBR (+0.51, 0, +1).
# Blue's mesh center is world (+0.51, +0.51, +0.5).
# Local offset from Blue's origin to its mesh center:
#   (0.51-0.51, 0.51-0, 0.5-1) = (0, +0.51, -0.5)
SEAT_BLUE_LOCAL   = mathutils.Vector((0.0, 0.51, -0.5))
# Yellow stays fixed. Geometric center in world: (-0.51, +0.51, +0.5).
SEAT_YELLOW_WORLD = mathutils.Vector((-0.51, 0.51, 0.5))


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
    for hn in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        h = bpy.data.objects.get(hn)
        if h:
            h.rotation_mode = 'XYZ'
            h.rotation_euler = (0.0, 0.0, 0.0)
    # Tear down stale parenting from prior runs so each Run starts clean.
    for name in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
                 "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj and obj.parent is not None:
            mw = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = mw
    for sn in ["Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
        s = bpy.data.objects.get(sn)
        if s: bpy.data.objects.remove(s, do_unlink=True)
    bpy.context.view_layer.update()


def set_last_keyframe_interpolation(obj, data_path, frame, interp='LINEAR'):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    fcurves = None
    try: fcurves = action.fcurves
    except AttributeError: pass
    if fcurves is None:
        try: fcurves = action.layers[0].strips[0].channelbag_for_slot(action.slots[0]).fcurves
        except Exception: pass
    if fcurves is None:
        try: fcurves = action.layers[0].strips[0].channelbags[0].fcurves
        except Exception: return
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


def key_influence(obj, cname, frame, value):
    bpy.context.scene.frame_set(frame)
    con = obj.constraints.get(cname)
    if not con: return
    con.influence = value
    dp = f'constraints["{cname}"].influence'
    obj.keyframe_insert(data_path=dp, frame=frame)
    set_last_keyframe_interpolation(obj, dp, frame, 'CONSTANT')


def parent_preserve_world(child, new_parent):
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw


def setup_blue_to_yellow():
    print("=== C15_REV Start: Blue → Yellow ===")
    reset_scene_to_canonical()
    blue   = bpy.data.objects.get("Cube_Blue")
    yellow = bpy.data.objects.get("Cube_Yellow")
    red    = bpy.data.objects.get("Cube_Red")
    ball   = bpy.data.objects.get("Ball")
    hinge  = bpy.data.objects.get("Hinge_Red_Green")
    missing = [n for n, o in [("Cube_Blue", blue), ("Cube_Yellow", yellow),
                              ("Cube_Red", red), ("Ball", ball),
                              ("Hinge_Red_Green", hinge)] if o is None]
    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    bpy.context.scene.frame_set(F_START)
    hinge.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # Chain: Red driven by HRG, Blue rides Red. Green and Yellow fixed.
    # Reverse of forward C15 — Blue+Red side of HRG folds instead.
    if red.parent != hinge:
        parent_preserve_world(red, hinge)
    if blue.parent != red:
        parent_preserve_world(blue, red)
    print("Chain: HRG ← Red ← Blue   (Green+Yellow fixed)")

    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try: bpy.ops.rigidbody.object_remove()
        except Exception:
            try: ball.rigid_body.kinematic = True
            except Exception: pass

    bpy.context.view_layer.update()
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()

    seat_blue_world = blue.matrix_world @ SEAT_BLUE_LOCAL
    seat_blue = bpy.data.objects.new("Seat_Blue", None)
    seat_blue.empty_display_type = 'SPHERE'
    seat_blue.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue)
    seat_blue.parent = blue
    seat_blue.location = SEAT_BLUE_LOCAL.copy()

    ball.matrix_world.translation = seat_blue_world.copy()
    bpy.context.view_layer.update()

    seat_yellow_local = yellow.matrix_world.inverted() @ SEAT_YELLOW_WORLD
    seat_yellow = bpy.data.objects.new("Seat_Yellow", None)
    seat_yellow.empty_display_type = 'SPHERE'
    seat_yellow.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_yellow)
    seat_yellow.parent = yellow
    seat_yellow.location = seat_yellow_local

    bpy.context.view_layer.update()

    latch_b = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_b.name = "Latch_Blue"
    latch_b.target = seat_blue
    latch_y = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_y.name = "Latch_Yellow"
    latch_y.target = seat_yellow

    key_rot(hinge, F_START,   0)
    key_rot(hinge, F_MID,    90)
    key_rot(hinge, F_HOLD,  180)
    key_rot(hinge, F_SWAP,  180)
    key_rot(hinge, F_RET,    90)
    key_rot(hinge, F_END,     0)

    key_influence(ball, "Latch_Blue",   F_START, 1.0)
    key_influence(ball, "Latch_Yellow", F_START, 0.0)
    key_influence(ball, "Latch_Blue",   F_HOLD,  1.0)
    key_influence(ball, "Latch_Yellow", F_HOLD,  0.0)
    key_influence(ball, "Latch_Blue",   F_SWAP,  0.0)
    key_influence(ball, "Latch_Yellow", F_SWAP,  1.0)
    key_influence(ball, "Latch_Blue",   F_END,   0.0)
    key_influence(ball, "Latch_Yellow", F_END,   1.0)

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)
    print("=== C15_REV Complete: Blue → Yellow ===")
    return True


class LORQB_OT_ResetC15Rev(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c15_rev"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        reset_scene_to_canonical()
        return {'FINISHED'}


class LORQB_OT_BlueToYellow(bpy.types.Operator):
    bl_idname  = "lorqb.blue_to_yellow"
    bl_label   = "Blue to Yellow C15_REV"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        ok = setup_blue_to_yellow()
        self.report({'INFO' if ok else 'ERROR'},
                    "C15_REV complete" if ok else "C15_REV failed")
        return {'FINISHED'}


class LORQB_PT_C15RevPanel(bpy.types.Panel):
    bl_label       = "LorQB C15_REV: Blue → Yellow"
    bl_idname      = "LORQB_PT_c15_rev_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'
    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c15_rev", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.blue_to_yellow", text="Run C15_REV: Blue → Yellow", icon='PLAY')


_classes = (LORQB_OT_ResetC15Rev, LORQB_OT_BlueToYellow, LORQB_PT_C15RevPanel)

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
