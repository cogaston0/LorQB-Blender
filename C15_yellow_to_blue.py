# ============================================================================
# C15_yellow_to_blue.py  (Blender 5.0.1)
# C15 — Yellow → Blue
# Frames 1 – 240 | Hinge snaps at frame 120
# Chain: Blue — Red — Green — Yellow
# Hinge: Hinge_Red_Green (Y-axis rotation, CONSTANT interpolation)
# NOTE: Hinge-rotation block — ball/seat/latch transfer to be added.
# Architecture: matches C12/C13/C14 reference standard
# ============================================================================

import bpy
import math

################################################################################
# SECTION 1: Constants
################################################################################
F_START  = 1
F_MID    = 120
F_END    = 240

ROT_AXIS = 1    # Y-axis index in rotation_euler

################################################################################
# SECTION 2: RESET — Clear Hinge_Red_Green animation and ball state
################################################################################
def reset_c15_state():
    hinge = bpy.data.objects.get("Hinge_Red_Green")
    if hinge and hinge.animation_data:
        hinge.animation_data_clear()
    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()
    bpy.context.view_layer.update()
    print("=== C15 state reset (Hinge_Red_Green + ball only) ===")

################################################################################
# SECTION 3: Helper — set interpolation on a specific keyframe by frame number
################################################################################
def set_last_keyframe_interpolation(obj, data_path, frame, interp='LINEAR'):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    try:
        fcurves = action.fcurves
    except AttributeError:
        try:
            fcurves = action.layers[0].strips[0].channelbag_for_slot(
                action.slots[0]
            ).fcurves
        except Exception:
            print(f"WARNING: Could not access fcurves for {obj.name} — skipping interpolation set")
            return
    for fc in fcurves:
        if fc.data_path == data_path or data_path in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp

################################################################################
# SECTION 4: Helper — key Y-axis rotation with CONSTANT interpolation (snap)
################################################################################
def key_rot_y_constant(obj, frame, degrees):
    bpy.context.scene.frame_set(frame)
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler[ROT_AXIS] = math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=frame)
    set_last_keyframe_interpolation(obj, "rotation_euler", frame, 'CONSTANT')

################################################################################
# SECTION 5: (Reserved — constraint-influence helpers not yet needed)
################################################################################

################################################################################
# SECTION 6: (Reserved — parent helper not yet needed)
################################################################################

################################################################################
# SECTION 7: Main C15 setup function
################################################################################
def setup_yellow_to_blue():
    print("=== C15 Start: Yellow → Blue ===")

    reset_c15_state()

    req = [
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Ball",
        "Hinge_Red_Green", "Hinge_Green_Yellow", "Hinge_Blue_Red",
    ]
    missing = [n for n in req if bpy.data.objects.get(n) is None]
    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    hinge = bpy.data.objects.get("Hinge_Red_Green")
    bpy.context.scene.frame_set(F_START)
    hinge.rotation_mode = 'XYZ'
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    key_rot_y_constant(hinge, F_START,   0)
    key_rot_y_constant(hinge, F_MID,   180)
    key_rot_y_constant(hinge, F_END,     0)
    print("Hinge_Red_Green rotation keyed — CONSTANT (snap).")

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== C15 Complete: Yellow → Blue ===")
    print(f"Frames {F_START}–{F_END} | Hinge snaps at frame {F_MID}")
    print("Axis: Y | Hinge: Hinge_Red_Green | Interpolation: CONSTANT")
    print("NOTE: Ball/seat/latch transfer block to be added in next iteration.")
    return True

################################################################################
# SECTION 8: Blender UI Panel and Operator
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
        col.label(text="Hinge_Red_Green: Y snap at frame 120")
        col.separator()
        col.label(text="● Blue → Red → Green → Yellow → Blue")

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
# SECTION 9: Register / Unregister
################################################################################
def _unregister_all_lorqb():
    to_remove = []
    for name in dir(bpy.types):
        cls = getattr(bpy.types, name, None)
        if cls is None:
            continue
        bl_idname = getattr(cls, "bl_idname", "") or ""
        if "lorqb" in bl_idname.lower():
            to_remove.append(cls)
    for cls in to_remove:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

def register():
    _unregister_all_lorqb()
    bpy.utils.register_class(LORQB_PT_C15Panel)
    bpy.utils.register_class(LORQB_OT_YellowToBlue)
    print("\n" + "=" * 50)
    print("✓ LorQB C15 Panel Ready.")
    print("3D View → N-panel → LorQB → 'Run C15: Yellow → Blue'")
    print("=" * 50 + "\n")

def unregister():
    try:
        bpy.utils.unregister_class(LORQB_OT_YellowToBlue)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(LORQB_PT_C15Panel)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
