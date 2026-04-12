# ============================================================================
# T01_blue_to_green.py  (Blender 5.0.1)
# T1 — Blue → Green
#
# Three moves, no detachment:
#   Stage 1  (  1– 80): HBR 180° — Blue flips over Red
#   Stage 2  ( 81–160): HRG  90° — whole system rotates, Blue lands on Green
#   Frame 161:          Ball transfers Blue → Green
#   Return   (162–200): HRG back to 0°
#   Return   (201–240): HBR back to 0°
#
# No detachment guarantee:
#   HRG is the root of the moving assembly. Red and Blue are children.
#   When HRG rotates (Stage 2), the entire assembly moves as one rigid body.
#   Green stays fixed (no parent) — it is the destination.
#
# Hierarchy:
#   HRG (root)
#   └── Red → HBR → Blue
#   Green (unparented — fixed destination)
# ============================================================================

import bpy
import math
import mathutils

###############################################################################
# SECTION 1: Constants
###############################################################################

F_START    = 1
F_S1_END   = 80     # HBR reaches 180°
F_S2_END   = 160    # HRG reaches 90°
F_SWAP     = 161    # Ball transfers Blue → Green
F_RET1_END = 200    # HRG back to 0°
F_RET2_END = 240    # HBR back to 0°
F_END      = 240

HBR_AXIS   = 0
HBR_SIGN   = +1.0
HBR_DEG    = 180.0

HRG_AXIS   = 1
HRG_SIGN   = +1.0
HRG_DEG    = 90.0

BALL_BLUE_INTERIOR   = mathutils.Vector(( 0.51,  0.51, 0.25))
SEAT_GREEN_WORLD     = mathutils.Vector((-0.51, -0.51, 0.25))

###############################################################################
# SECTION 2: Reset
###############################################################################

def reset_scene_to_canonical():
    for name in ["Ball",
                 "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
                 "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    for name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        h = bpy.data.objects.get(name)
        if h:
            h.rotation_mode  = 'XYZ'
            h.rotation_euler = (0.0, 0.0, 0.0)

    for name in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
                 "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.parent = None

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

    for name in ["Seat_Blue_Start", "Seat_Green",
                 "Seat_Blue", "Seat_Red", "Seat_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.context.view_layer.update()
    print("=== T1 reset to canonical ===")

###############################################################################
# SECTION 3: Helpers
###############################################################################

def _fcurves(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return []
    try:
        return obj.animation_data.action.layers[0].strips[0].channelbags[0].fcurves
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
        print(f"WARNING: constraint '{con_name}' not found")
        return
    con.influence = value
    dp = f'constraints["{con_name}"].influence'
    obj.keyframe_insert(data_path=dp, frame=frame)
    for fc in _fcurves(obj):
        if con_name in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = 'CONSTANT'

###############################################################################
# SECTION 4: Animation
###############################################################################

def run_animation():
    print("=== T1 Start: Blue → Green ===")
    reset_scene_to_canonical()

    blue     = bpy.data.objects.get("Cube_Blue")
    red      = bpy.data.objects.get("Cube_Red")
    green    = bpy.data.objects.get("Cube_Green")
    ball     = bpy.data.objects.get("Ball")
    hinge_br = bpy.data.objects.get("Hinge_Blue_Red")
    hinge_rg = bpy.data.objects.get("Hinge_Red_Green")

    missing = [n for n, o in [
        ("Cube_Blue",       blue),
        ("Cube_Red",        red),
        ("Cube_Green",      green),
        ("Ball",            ball),
        ("Hinge_Blue_Red",  hinge_br),
        ("Hinge_Red_Green", hinge_rg),
    ] if o is None]
    if missing:
        print("ERROR: Missing:", missing)
        return False

    # ── Zero hinges ──────────────────────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    for h in (hinge_br, hinge_rg):
        h.rotation_mode  = 'XYZ'
        h.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # ── Build hierarchy — HRG is root of moving assembly ────────────────────
    # Identity matrix_parent_inverse prevents stale-matrix jumps on re-run.
    # Green stays unparented — it is the fixed destination.
    I4 = mathutils.Matrix.Identity(4)

    def attach(child, parent, local_xyz):
        child.parent                = parent
        child.matrix_parent_inverse = I4.copy()
        child.location              = local_xyz
        child.rotation_euler        = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

    # HRG → Red → HBR → Blue
    attach(red,      hinge_rg, ( 0.0,   0.0,  0.0))
    attach(hinge_br, red,      ( 0.51,  0.51, 0.0))
    attach(blue,     hinge_br, ( 0.0,   0.0,  0.0))

    print("Hierarchy: HRG(root) → Red → HBR → Blue  (Green fixed)")

    # ── Remove rigid body from ball ──────────────────────────────────────────
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    # ── Place ball inside Blue ───────────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    ball.location = BALL_BLUE_INTERIOR.copy()
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()

    # ── Seats ────────────────────────────────────────────────────────────────
    ball_world = ball.matrix_world.translation.copy()

    seat_blue_start = bpy.data.objects.new("Seat_Blue_Start", None)
    seat_blue_start.empty_display_type = 'SPHERE'
    seat_blue_start.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue_start)
    seat_blue_start.parent   = blue
    seat_blue_start.location = blue.matrix_world.inverted() @ ball_world

    seat_green = bpy.data.objects.new("Seat_Green", None)
    seat_green.empty_display_type = 'SPHERE'
    seat_green.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_green)
    seat_green.parent   = green
    seat_green.location = green.matrix_world.inverted() @ SEAT_GREEN_WORLD

    bpy.context.view_layer.update()

    # ── Ball constraints ─────────────────────────────────────────────────────
    latch_blue = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_blue.name   = "Latch_Blue_Start"
    latch_blue.target = seat_blue_start

    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name   = "Latch_Green"
    latch_green.target = seat_green

    # ── Stage 1 — HBR 0°→180° (Blue flips over Red) ─────────────────────────
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_START,    0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S1_END,   HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S2_END,   HBR_DEG)   # hold during Stage 2
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_SWAP,     HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET1_END, HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET2_END, 0)

    # ── Stage 2 — HRG 0°→90° (whole system — Blue lands on Green) ───────────
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_START,    0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S1_END,   0)          # hold during Stage 1
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2_END,   HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_SWAP,     HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET1_END, 0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET2_END, 0)

    # ── Ball transfer at frame 161 ───────────────────────────────────────────
    key_influence(ball, "Latch_Blue_Start", F_START,   1.0)
    key_influence(ball, "Latch_Green",      F_START,   0.0)
    key_influence(ball, "Latch_Blue_Start", F_S2_END,  1.0)
    key_influence(ball, "Latch_Green",      F_S2_END,  0.0)
    key_influence(ball, "Latch_Blue_Start", F_SWAP,    0.0)
    key_influence(ball, "Latch_Green",      F_SWAP,    1.0)
    key_influence(ball, "Latch_Blue_Start", F_END,     0.0)
    key_influence(ball, "Latch_Green",      F_END,     1.0)

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== T1 Complete: Blue → Green ===")
    print("Stage 1 (1–80):    HBR 180° — Blue flips over Red")
    print("Stage 2 (81–160):  HRG  90° — whole system, Blue on Green")
    print("Frame 161: ball transfers")
    return True

###############################################################################
# SECTION 5: UI Panel
###############################################################################

class LORQB_OT_reset_t1(bpy.types.Operator):
    bl_idname      = "lorqb.reset_t1"
    bl_label       = "Reset to Base"
    bl_description = "Reset all objects to canonical state"

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "T1 reset to base")
        return {'FINISHED'}

class LORQB_OT_run_t1(bpy.types.Operator):
    bl_idname      = "lorqb.run_t1"
    bl_label       = "Run T1: Blue → Green"
    bl_description = "Arm T1 animation: Blue transfers ball to Green"

    def execute(self, context):
        result = run_animation()
        if result:
            self.report({'INFO'}, "T1 armed — press Play to run")
        else:
            self.report({'ERROR'}, "T1 failed — check console")
        return {'FINISHED'}

class LORQB_PT_t1_panel(bpy.types.Panel):
    bl_label       = "LorQB — T1"
    bl_idname      = "LORQB_PT_t1_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_t1", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.run_t1",   text="Run T1: Blue → Green", icon='PLAY')

_classes = [LORQB_OT_reset_t1, LORQB_OT_run_t1, LORQB_PT_t1_panel]

###############################################################################
# SECTION 6: Register / Entry Point
###############################################################################

def register():
    for name in ["LORQB_PT_t1_panel", "LORQB_OT_run_t1", "LORQB_OT_reset_t1"]:
        cls = getattr(bpy.types, name, None)
        if cls:
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass
    for cls in _classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

register()
