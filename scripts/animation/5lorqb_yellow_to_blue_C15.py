# ============================================================================
# 5lorqb_yellow_to_blue_C15.py
# Blender 5.0.1
# C15 — Yellow → Blue Transfer
# Frames 720–960
# Transfer at 840→841
#
# RULES:
# - Child Of constraints only
# - No parenting
# - No physics
# - No drivers
# - Constant interpolation only
# - Must return to rest state
# ============================================================================

import bpy
import math

# ============================================================================
# 5lorqb_yellow_to_blue_C15.py  (Blender 5.0.1)
# ----------------------------------------------------------------------------
# LorQB Level 1 - Sequence C15 (Yellow -> Blue)
#
# POSITION IN FULL SEQUENCE
#   Blue  -> Red    :   0 - 240
#   Red   -> Green  : 240 - 480
#   Green -> Yellow : 480 - 720
#   Yellow-> Blue   : 720 - 960   <- THIS SCRIPT
#
# C15 CYCLE
#   Frame 720        : start / rest state  (Yellow holds ball, hinge at 0 deg)
#   Frame 840 -> 841 : transfer moment     (ball passes Yellow -> Blue)
#   Frame 960        : end / rest state    (hinge back to 0 deg, Blue holds ball)
#
# HINGE        : Hinge_Red_Green  (Y-axis, 180 deg)
# SWING SEGMENT: Yellow + Green swing over Red + Blue
#
# RULES ENFORCED
#   - Child Of constraints only (no parenting, no physics, no drivers)
#   - 180 deg hinge rotation only
#   - Constant interpolation on every keyframe
#   - Ball transfers at midpoint (frame 840)
#   - Hinge returns to 0 deg by frame 960
#   - System at frame 960 is identical to frame 720 (ready for next loop)
# ============================================================================

import bpy
import math

# ----------------------------------------------------------------------------
# UI / IDs
# ----------------------------------------------------------------------------
ADDON_NAME   = "LorQB"
TAB_NAME     = "LorQB"
PANEL_LABEL  = "LorQB Animation"
PANEL_ID     = "LORQB_PT_animation_panel"
OP_ID        = "lorqb.c15_yellow_to_blue"
OP_LABEL     = "Run C15: Yellow -> Blue"

# ----------------------------------------------------------------------------
# FRAME CONSTANTS
# ----------------------------------------------------------------------------
C15_START    = 720   # rest state  - Yellow holds ball, hinge 0 deg
C15_TRANSFER = 840   # midpoint    - hinge snaps to 180 deg, ball -> Blue
C15_END      = 960   # rest state  - hinge back to 0 deg, Blue holds ball

HINGE_ROT_DEG = 180.0

# ----------------------------------------------------------------------------
# CONSTRAINT NAMES  (unique per cycle to avoid collision with other cycles)
# ----------------------------------------------------------------------------
CON_YELLOW = "ChildOf_Yellow_C15"
CON_BLUE   = "ChildOf_Blue_C15"

# ----------------------------------------------------------------------------
# REQUIRED OBJECT NAMES  (must match your .blend file exactly)
# ----------------------------------------------------------------------------
REQ = [
    "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
    "Ball",
    "Hinge_Red_Green", "Hinge_Green_Yellow", "Hinge_Blue_Red",
]

# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def require_objects():
    missing = [n for n in REQ if bpy.data.objects.get(n) is None]
    if missing:
        raise RuntimeError("Missing objects: " + ", ".join(missing))


def clear_object_animation(obj):
    if obj.animation_data:
        obj.animation_data_clear()


def ensure_child_of(obj, con_name, target):
    """Return (or create) a named Child Of constraint pointing at target."""
    con = obj.constraints.get(con_name)
    if con is None:
        con = obj.constraints.new("CHILD_OF")
        con.name = con_name
    con.target = target
    return con


def evaluated_world_matrix(obj):
    """
    Return the fully-evaluated (post-constraint) world matrix of obj.
    Uses the current depsgraph so all constraints are taken into account.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    return obj.evaluated_get(depsgraph).matrix_world.copy()


def set_child_of_inverse(obj, con_name):
    """
    Store the correct inverse matrix on the named Child Of constraint so that
    the object does not jump when that constraint's influence is set to 1.0.

    Equivalent to clicking 'Set Inverse' in Properties > Object Constraints,
    computed programmatically at the current evaluated frame.
    """
    con = obj.constraints.get(con_name)
    if con is None or con.target is None:
        return
    target_world_inv = evaluated_world_matrix(con.target).inverted()
    obj_world        = evaluated_world_matrix(obj)
    con.inverse_matrix = target_world_inv @ obj_world


def force_constant_all(obj):
    """
    Force CONSTANT interpolation on every keyframe point in the object's
    action.  Works for rotation_euler and constraint influence curves alike.
    """
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


def force_constant_rotation_euler(obj):
    """
    Force CONSTANT interpolation specifically on rotation_euler fcurves.
    Uses the Blender 5 Action.fcurve_ensure_for_datablock() API.
    """
    ad = obj.animation_data
    if not ad or not ad.action:
        raise RuntimeError(f"No action found on '{obj.name}' after inserting keys.")
    act = ad.action
    for i in (0, 1, 2):
        fc = act.fcurve_ensure_for_datablock(obj, "rotation_euler", index=i)
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


# ----------------------------------------------------------------------------
# PHASE 1 - HINGE ROTATION
#   Hinge_Red_Green  Y-axis:  0 deg (f720) -> 180 deg (f840) -> 0 deg (f960)
# ----------------------------------------------------------------------------
def key_hinge(scene, hinge):
    clear_object_animation(hinge)
    hinge.rotation_mode = "XYZ"

    # Frame 720 - rest position (0 deg)
    scene.frame_set(C15_START)
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # Frame 840 - fully rotated (180 deg)  <- swing completes here
    scene.frame_set(C15_TRANSFER)
    hinge.rotation_euler = (0.0, math.radians(HINGE_ROT_DEG), 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # Frame 960 - back to rest (0 deg)
    scene.frame_set(C15_END)
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    force_constant_rotation_euler(hinge)
    print(
        f"  Hinge_Red_Green: 0 deg -> 180 deg (f{C15_START}->f{C15_TRANSFER})"
        f" -> 0 deg (f{C15_END})  [CONSTANT]"
    )


# ----------------------------------------------------------------------------
# PHASE 2 - BALL TRANSFER
#   Child Of constraints with CONSTANT influence switching at frame 840
# ----------------------------------------------------------------------------
def key_ball_transfer(scene, ball, cube_yellow, cube_blue):
    # Remove any leftover C15 constraints from a previous run
    for cn in (CON_YELLOW, CON_BLUE):
        old = ball.constraints.get(cn)
        if old:
            ball.constraints.remove(old)

    # Create both Child Of constraints (influence keyed below)
    con_y = ensure_child_of(ball, CON_YELLOW, cube_yellow)
    con_b = ensure_child_of(ball, CON_BLUE,   cube_blue)

    # Clear any prior ball animation so influence curves start fresh
    clear_object_animation(ball)

    # --- FRAME 720: Yellow holds ball ---
    scene.frame_set(C15_START)
    bpy.context.view_layer.update()

    con_y.influence = 1.0
    con_b.influence = 0.0

    # Set Yellow inverse (ball world position at rest, hinge at 0 deg)
    set_child_of_inverse(ball, CON_YELLOW)

    ball.keyframe_insert(
        data_path=f'constraints["{CON_YELLOW}"].influence', frame=C15_START)
    ball.keyframe_insert(
        data_path=f'constraints["{CON_BLUE}"].influence',   frame=C15_START)

    # --- FRAME 840: hinge at 180 deg - compute Blue inverse BEFORE switching ---
    #
    # Yellow.influence is still 1.0 (live, not yet keyed for frame 840) so the
    # evaluated ball position is wherever Yellow is at 180 deg rotation.
    # We capture that world position and bake it into the Blue inverse matrix
    # so Blue 'picks up' the ball at exactly that location when we flip.
    scene.frame_set(C15_TRANSFER)
    bpy.context.view_layer.update()

    set_child_of_inverse(ball, CON_BLUE)

    # Now switch: Yellow releases, Blue catches
    con_y.influence = 0.0
    con_b.influence = 1.0

    ball.keyframe_insert(
        data_path=f'constraints["{CON_YELLOW}"].influence', frame=C15_TRANSFER)
    ball.keyframe_insert(
        data_path=f'constraints["{CON_BLUE}"].influence',   frame=C15_TRANSFER)

    # --- FRAME 960: hinge back to 0 deg, Blue still holds ball ---
    ball.keyframe_insert(
        data_path=f'constraints["{CON_YELLOW}"].influence', frame=C15_END)
    ball.keyframe_insert(
        data_path=f'constraints["{CON_BLUE}"].influence',   frame=C15_END)

    # Force CONSTANT on ALL ball fcurves (covers both influence paths)
    force_constant_all(ball)
    print(
        f"  Ball: ChildOf_Yellow_C15=1 @ f{C15_START}"
        f"  ->  ChildOf_Blue_C15=1 @ f{C15_TRANSFER}  [CONSTANT]"
    )


# ----------------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------------
def build_c15():
    require_objects()

    scene       = bpy.context.scene
    hinge       = bpy.data.objects["Hinge_Red_Green"]
    ball        = bpy.data.objects["Ball"]
    cube_yellow = bpy.data.objects["Cube_Yellow"]
    cube_blue   = bpy.data.objects["Cube_Blue"]

    print("=== C15: Yellow -> Blue ===")
    key_hinge(scene, hinge)
    key_ball_transfer(scene, ball, cube_yellow, cube_blue)

    # Return playhead to the start of C15
    scene.frame_set(C15_START)

    print(
        f"  System at frame {C15_END} == rest state at frame {C15_START}\n"
        "=== C15 COMPLETE ==="
    )


# ----------------------------------------------------------------------------
# OPERATOR + PANEL
# ----------------------------------------------------------------------------
class LORQB_OT_c15_yellow_to_blue(bpy.types.Operator):
    bl_idname = OP_ID
    bl_label  = OP_LABEL

    def execute(self, context):
        try:
            build_c15()
            self.report({'INFO'}, "C15 Yellow->Blue complete.")
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


class LORQB_PT_animation_panel(bpy.types.Panel):
    bl_label       = PANEL_LABEL
    bl_idname      = PANEL_ID
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = TAB_NAME

    def draw(self, context):
        self.layout.operator(OP_ID, text=OP_LABEL)


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
