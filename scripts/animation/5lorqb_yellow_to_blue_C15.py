# ============================================================================
# 5lorqb_yellow_to_blue_C15.py  (Blender 5.0.1)
# ----------------------------------------------------------------------------
# LorQB Level 1 -- Sequence C15  (Yellow -> Blue)
#
# POSITION IN FULL SEQUENCE:
#   Blue -> Red:          0 - 240
#   Red  -> Green:      240 - 480
#   Green -> Yellow:    480 - 720
#   Yellow -> Blue (C15): 720 - 960   <- this script
#
# C15 CYCLE:
#   Start frame:          720
#   Transfer moment:  840 -> 841
#   End / rest:           960
#   Duration:         240 frames
#
# RULES:
#   - Child Of constraints only (no parenting, no physics, no drivers)
#   - 180 deg hinge rotation on Y-axis only
#   - Constant interpolation only
#   - Ball transfers at midpoint (frame 840 -> 841)
#   - Hinge returns to 0 deg by frame 960
#   - System returns to rest state identical to frame 720
#
# HINGE:           Hinge_Red_Green  (Y-axis)
# SWINGING SIDE:   Yellow + Green swing over Red + Blue
# ============================================================================

import bpy
import math

# ----------------------------------------------------------------------------
# UI / IDs
# ----------------------------------------------------------------------------
TAB_NAME    = "LorQB"
PANEL_LABEL = "LorQB Animation"
PANEL_ID    = "LORQB_PT_animation_panel"
OP_ID       = "lorqb.c15_yellow_to_blue"
OP_LABEL    = "Run C15: Yellow -> Blue"

# ----------------------------------------------------------------------------
# OBJECT NAMES  (must match your .blend file)
# ----------------------------------------------------------------------------
OBJ_HINGE       = "Hinge_Red_Green"
OBJ_BALL        = "Ball"
OBJ_SEAT_YELLOW = "Cube_Yellow"   # Yellow arm -- moves WITH the hinge
OBJ_SEAT_BLUE   = "Cube_Blue"     # Blue  arm  -- stationary during C15

CON_YELLOW = "C15_Child_Yellow"
CON_BLUE   = "C15_Child_Blue"

REQ = [
    "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
    "Ball",
    "Hinge_Red_Green", "Hinge_Green_Yellow", "Hinge_Blue_Red",
]

# ----------------------------------------------------------------------------
# FRAME CONSTANTS
# ----------------------------------------------------------------------------
F_START      = 720   # C15 begins; hinge at 0 deg; ball in Yellow seat
F_TRANSFER   = 840   # hinge snaps to 180 deg (CONSTANT key); ball still Yellow
F_TRANSFER_1 = 841   # ball switches to Blue (first frame owned by Blue)
F_END        = 960   # hinge returns to 0 deg; system at rest

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


def _force_constant_on_action(obj, data_path_fragment):
    """Force CONSTANT interpolation on every fcurve whose data_path contains
    *data_path_fragment*.  Supports both the classic .fcurves attribute and the
    Blender 5 layered-action structure (layers -> strips -> fcurves)."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    act = ad.action

    # Blender 5 layered action
    try:
        for layer in act.layers:
            for strip in layer.strips:
                for fc in strip.fcurves:
                    if data_path_fragment in fc.data_path:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "CONSTANT"
        return
    except AttributeError:
        pass

    # Classic action (pre-5 fallback)
    try:
        for fc in act.fcurves:
            if data_path_fragment in fc.data_path:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
    except AttributeError:
        pass


def force_constant_rotation_euler(obj):
    """Force CONSTANT on all rotation_euler channels of *obj*."""
    ad = obj.animation_data
    if not ad or not ad.action:
        raise RuntimeError("No action on {} after inserting rotation keyframes.".format(obj.name))
    act = ad.action
    try:
        # Blender 5.0.1: fcurve_ensure_for_datablock
        for i in (0, 1, 2):
            fc = act.fcurve_ensure_for_datablock(obj, "rotation_euler", index=i)
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
    except AttributeError:
        _force_constant_on_action(obj, "rotation_euler")


def force_constant_constraint_influence(ball, con_name):
    """Force CONSTANT on the influence fcurve for *con_name* on *ball*."""
    _force_constant_on_action(ball, 'constraints["{}"].influence'.format(con_name))


def get_or_add_child_of(ball, name, target):
    """Return existing Child Of constraint (or create a new one)."""
    con = ball.constraints.get(name)
    if con is None:
        con = ball.constraints.new("CHILD_OF")
        con.name = name
    con.target = target
    con.use_location_x = True
    con.use_location_y = True
    con.use_location_z = True
    con.use_rotation_x = True
    con.use_rotation_y = True
    con.use_rotation_z = True
    con.use_scale_x    = True
    con.use_scale_y    = True
    con.use_scale_z    = True
    return con


def set_child_of_inverse(ball, con):
    """Equivalent to pressing 'Set Inverse' in the UI.
    Call AFTER frame_set + view_layer.update() so ball.matrix_world reflects
    the desired world position."""
    bpy.context.view_layer.update()
    if con.target:
        # Transforms ball's world position into target's local space:
        # inverse_matrix = target_world_inv @ ball_world
        con.inverse_matrix = con.target.matrix_world.inverted() @ ball.matrix_world


# ----------------------------------------------------------------------------
# MAIN ANIMATION FUNCTION
# ----------------------------------------------------------------------------
def key_c15():
    require_objects()

    scene  = bpy.context.scene
    hinge  = bpy.data.objects[OBJ_HINGE]
    ball   = bpy.data.objects[OBJ_BALL]
    seat_y = bpy.data.objects[OBJ_SEAT_YELLOW]
    seat_b = bpy.data.objects[OBJ_SEAT_BLUE]

    # ---------------------------------------------------------------- HINGE --
    # Wipe prior animation so we don't stack transforms
    clear_object_animation(hinge)
    hinge.rotation_mode = "XYZ"

    # Frame 720 -- rest / 0 deg
    scene.frame_set(F_START)
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # Frame 840 -- 180 deg snap  (transfer moment; ball still owned by Yellow)
    scene.frame_set(F_TRANSFER)
    hinge.rotation_euler = (0.0, math.radians(180.0), 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # Frame 960 -- return to 0 deg / rest
    scene.frame_set(F_END)
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    force_constant_rotation_euler(hinge)

    # ------------------------------------------------ BALL CHILD OF SETUP  --
    # Ensure both constraints exist on Ball
    con_y = get_or_add_child_of(ball, CON_YELLOW, seat_y)
    con_b = get_or_add_child_of(ball, CON_BLUE,   seat_b)

    # Clear any previous Ball animation so influences start clean
    clear_object_animation(ball)

    # ---- Frame 720: ball sits in Yellow seat (hinge = 0 deg) ----
    scene.frame_set(F_START)
    con_y.influence = 1.0
    con_b.influence = 0.0
    # Set Yellow inverse so ball is locked to its current Yellow-seat position
    set_child_of_inverse(ball, con_y)
    # Key influences at start
    con_y.keyframe_insert(data_path="influence")
    con_b.keyframe_insert(data_path="influence")

    # ---- Frame 840: hinge at 180 deg; ball (via Yellow) is now above Blue ----
    # Capture Blue's inverse HERE (before the influence switch at 841) so that
    # ball.matrix_world reflects the Yellow-carried world position over Blue.
    # This ensures no teleport when Blue takes ownership at F_TRANSFER_1.
    scene.frame_set(F_TRANSFER)
    bpy.context.view_layer.update()
    # ball.matrix_world now reflects Yellow-carried position over Blue seat
    set_child_of_inverse(ball, con_b)

    # ---- Frame 841: ball transfers to Blue ----
    scene.frame_set(F_TRANSFER_1)
    con_y.influence = 0.0
    con_b.influence = 1.0
    con_y.keyframe_insert(data_path="influence")
    con_b.keyframe_insert(data_path="influence")

    # Force CONSTANT on both influence curves (no sliding, clean snap)
    force_constant_constraint_influence(ball, CON_YELLOW)
    force_constant_constraint_influence(ball, CON_BLUE)

    # Return to start frame for review
    scene.frame_set(F_START)

    print("C15 OK: Hinge_Red_Green  0->180->0 deg  (frames 720/840/960)  CONSTANT")
    print("C15 OK: Ball Yellow->Blue transfer at frame 841  CONSTANT")
    print("C15 OK: System returns to rest state at frame 960 -- ready for loop")


# ----------------------------------------------------------------------------
# OPERATOR + PANEL
# ----------------------------------------------------------------------------
class LORQB_OT_c15_yellow_to_blue(bpy.types.Operator):
    bl_idname = OP_ID
    bl_label  = OP_LABEL

    def execute(self, context):
        try:
            key_c15()
        except Exception as e:
            self.report({'ERROR'}, str(e))
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
