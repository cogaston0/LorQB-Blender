# ============================================================================
# 5lorqb_yellow_to_blue_C15.py  (Blender 5.0.1)
# ----------------------------------------------------------------------------
# LorQB Level 1 — Sequence C15 (Yellow -> Blue)
# Hinge: Hinge_Red_Green
# Axis: Y
#
# This script matches the *structure* of your C12/C13/C14 scripts:
# - Creates a LorQB UI tab + button
# - Runs a single operator that builds the C15 hinge rotation keys
# - Forces CONSTANT interpolation via Blender 5 Action API
# - Includes ball/seat/latch transfer block (same pattern as C13)
#
# Sequence: Green rotates via Hinge_Red_Green (Y axis) to align above Red.
# Ball transfers from Seat_Green to Seat_Red at frame 121 (CONSTANT swap).
# Yellow is passively carried by Green throughout the rotation.
# ============================================================================

import bpy
import math
import mathutils

# ----------------------------------------------------------------------------
# Frame constants
# ----------------------------------------------------------------------------
F_START = 1
F_HOLD  = 120   # Hinge at 180° — Green aligned above Red
F_SWAP  = 121   # Ball transfers from Seat_Green to Seat_Red
F_END   = 240   # Hinge back at 0°, ball in Red

# World-space seat positions (bottom-centre of each cube)
SEAT_GREEN_WORLD = mathutils.Vector((-0.51, -0.51, 0.25))
SEAT_RED_WORLD   = mathutils.Vector(( 0.51, -0.51, 0.25))

# ----------------------------------------------------------------------------
# UI / IDs
# ----------------------------------------------------------------------------
ADDON_NAME   = "LorQB"
TAB_NAME     = "LorQB"
PANEL_LABEL  = "LorQB Animation"
PANEL_ID     = "LORQB_PT_animation_panel"
OP_ID        = "lorqb.c15_yellow_to_blue"
OP_LABEL     = "Run C15: Yellow -> Blue (Hinge_Red_Green)"

# ----------------------------------------------------------------------------
# REQUIRED OBJECT NAMES (MATCH YOUR FILE)
# ----------------------------------------------------------------------------
REQ = [
    "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
    "Ball",
    "Hinge_Red_Green", "Hinge_Green_Yellow", "Hinge_Blue_Red",
]

# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def parent_preserve_world(child, new_parent):
    """Parent child to new_parent while keeping child's world transform."""
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw

def key_influence(obj, constraint_name, frame, value):
    """Insert constraint influence keyframe."""
    bpy.context.scene.frame_set(frame)
    con = obj.constraints.get(constraint_name)
    if not con:
        print(f"WARNING: Constraint '{constraint_name}' not found on {obj.name}")
        return
    con.influence = value
    obj.keyframe_insert(
        data_path=f'constraints["{constraint_name}"].influence',
        frame=frame
    )

def require_objects():
    missing = [n for n in REQ if bpy.data.objects.get(n) is None]
    if missing:
        raise RuntimeError("Missing objects: " + ", ".join(missing))

def clear_object_animation(obj: bpy.types.Object):
    if obj.animation_data:
        obj.animation_data_clear()

def force_constant_rotation_euler(obj: bpy.types.Object):
    """
    Blender 5.0.1 in your build:
    - Action has NO .fcurves
    - Use action.fcurve_ensure_for_datablock(..., index=)
    """
    ad = obj.animation_data
    if not ad or not ad.action:
        raise RuntimeError(f"No action found on {obj.name} after inserting keys.")

    act = ad.action

    # rotation_euler has 3 components: X=0, Y=1, Z=2
    for i in (0, 1, 2):
        fc = act.fcurve_ensure_for_datablock(obj, "rotation_euler", index=i)
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"

def key_hinge_red_green_C15():
    require_objects()

    hinge  = bpy.data.objects["Hinge_Red_Green"]
    green  = bpy.data.objects["Cube_Green"]
    yellow = bpy.data.objects["Cube_Yellow"]
    red    = bpy.data.objects["Cube_Red"]
    ball   = bpy.data.objects["Ball"]
    scene  = bpy.context.scene

    # --- Parent Green to Hinge_Red_Green (Green rotates); Yellow rides along ---
    if green.parent != hinge:
        parent_preserve_world(green, hinge)
        print("Green parented to Hinge_Red_Green.")
    if yellow.parent != green:
        parent_preserve_world(yellow, green)
        print("Yellow parented to Cube_Green — passive carry.")

    # wipe prior animation so we don’t “stack” rotations
    clear_object_animation(hinge)

    hinge.rotation_mode = "XYZ"

    # --- Hinge rotation keyframes ---
    # f1 = 0°
    scene.frame_set(F_START)
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # f120 = 180° on Y (Green aligned above Red)
    scene.frame_set(F_HOLD)
    hinge.rotation_euler = (0.0, math.radians(180.0), 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # f121 = 180° hold (swap frame)
    scene.frame_set(F_SWAP)
    hinge.rotation_euler = (0.0, math.radians(180.0), 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # f240 = 0° (back to rest, ball now in Red)
    scene.frame_set(F_END)
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # force snap
    force_constant_rotation_euler(hinge)
    print("C15 OK: Hinge_Red_Green keyed (Y: 0 -> 180 -> 0) with CONSTANT interpolation.")

    # --- Seat empties ---
    seat_green = bpy.data.objects.get("Seat_Green")
    if seat_green:
        bpy.data.objects.remove(seat_green, do_unlink=True)
    seat_green = bpy.data.objects.new("Seat_Green", None)
    seat_green.empty_display_type = 'SPHERE'
    seat_green.empty_display_size = 0.08
    scene.collection.objects.link(seat_green)
    seat_green.parent = green
    seat_green.location = green.matrix_world.inverted() @ SEAT_GREEN_WORLD
    print("Seat_Green created inside Cube_Green.")

    seat_red = bpy.data.objects.get("Seat_Red")
    if seat_red:
        bpy.data.objects.remove(seat_red, do_unlink=True)
    seat_red = bpy.data.objects.new("Seat_Red", None)
    seat_red.empty_display_type = 'SPHERE'
    seat_red.empty_display_size = 0.08
    scene.collection.objects.link(seat_red)
    seat_red.parent = red
    seat_red.location = red.matrix_world.inverted() @ SEAT_RED_WORLD
    print("Seat_Red created inside Cube_Red.")

    # --- Ball COPY_TRANSFORMS constraints ---
    ball.constraints.clear()

    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name = "Latch_Green"
    latch_green.target = seat_green
    print("Latch_Green created.")

    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name = "Latch_Red"
    latch_red.target = seat_red
    print("Latch_Red created.")

    # --- Constraint influence keyframes ---
    # Before swap: ball in Green (Latch_Green=1, Latch_Red=0)
    # After swap:  ball in Red  (Latch_Green=0, Latch_Red=1)
    key_influence(ball, "Latch_Green", F_START, 1.0)
    key_influence(ball, "Latch_Red",   F_START, 0.0)
    key_influence(ball, "Latch_Green", F_HOLD,  1.0)
    key_influence(ball, "Latch_Red",   F_HOLD,  0.0)
    key_influence(ball, "Latch_Green", F_SWAP,  0.0)
    key_influence(ball, "Latch_Red",   F_SWAP,  1.0)
    key_influence(ball, "Latch_Green", F_END,   0.0)
    key_influence(ball, "Latch_Red",   F_END,   1.0)
    print("Ball influences keyed.")

    # --- Frame range ---
    scene.frame_start = F_START
    scene.frame_end   = F_END
    scene.frame_set(F_START)

    print("=== C15 Complete: Green -> Red (Yellow -> Blue sequence) ===")
    print(f"Frames {F_START}-{F_END} | Transfer at frame {F_SWAP}")
    print("Green aligned above Red at frame", F_HOLD)
    print("WARNING: Set hinge keys to LINEAR and influence keys to CONSTANT")
    print("         manually in Graph Editor — same approach as C13.")
# ----------------------------------------------------------------------------
# OPERATOR + PANEL (THIS IS WHY YOU DIDN'T SEE A LorQB TAB BEFORE)
# ----------------------------------------------------------------------------
class LORQB_OT_c15_yellow_to_blue(bpy.types.Operator):
    bl_idname = OP_ID
    bl_label = OP_LABEL

    def execute(self, context):
        key_hinge_red_green_C15()
        self.report({'INFO'}, "C15 complete: Green -> Red (ball/seat/latch transfer done)")
        return {'FINISHED'}

class LORQB_PT_animation_panel(bpy.types.Panel):
    bl_label = PANEL_LABEL
    bl_idname = PANEL_ID
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = TAB_NAME

    def draw(self, context):
        layout = self.layout
        layout.operator(OP_ID, text=OP_LABEL)

# ----------------------------------------------------------------------------
# REGISTER
# ----------------------------------------------------------------------------
classes = (
    LORQB_OT_c15_yellow_to_blue,
    LORQB_PT_animation_panel,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()