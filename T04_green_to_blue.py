# ============================================================================
# T04_green_to_blue.py  (Blender 5.0.1)
# T4 — Green → Blue  (mirror of T03 Red → Yellow)
#
# Three moves, no detachment:
#   Stage 1  (  1– 80): HBR 180° — Blue opens toward Green      [mirrors HGY 180° in T03]
#   Stage 2a ( 81–120): Green 90° — Cube_Green rotates toward Blue [mirrors Red 90° in T03]
#   Stage 2b (121–160): HRG  90° — whole system, Green lands on Blue [same mechanism as T03]
#   Frame 161:          Ball transfers Green → Blue
#   Return   (162–200): HRG + Green back to 0°
#   Return   (201–240): HBR back to 0°
#
# Mirror logic (T03 → T04):
#   Yellow (destination, opened 180°) → Blue
#   HGY    (destination hinge, 180°)  → HBR
#   Red    (source, rotates 90° 2a)   → Green
#   HBR    (passive bridge in T03)    → HGY  (passive bridge in T04)
#   Blue   (passive in T03)           → Yellow (passive in T04)
#
# No detachment guarantee:
#   HRG is the world root. Every cube and hinge is a child.
#   Rotations move the tree — no child is ever unparented mid-animation.
#
# Hierarchy:
#   HRG (root)
#   ├── Red  → HBR → Blue   (Red passive bridge; HBR opens Blue in Stage 1)
#   └── HGY  → Green        (HGY passive; Green rotates in Stage 2a)
#                └── Yellow  (passive rider)
#
# Sign notes — mirrored from T03:
#   HBR_SIGN  = +1.0  (same as HGY_SIGN in T03 — symmetric opening)
#   GREEN_SIGN = +1.0  (opposite of RED_SIGN=-1.0 in T03 — mirrored geometry)
#   HRG_SIGN  = +1.0  (opposite of HRG_SIGN=-1.0 in T03 — system swings other way)
#   If a stage goes the wrong direction, flip its sign.
# ============================================================================

import bpy
import math
import mathutils

###############################################################################
# SECTION 1: Constants
###############################################################################

F_START    = 1
F_S1_END   = 80     # HBR reaches 180° — Blue fully open
F_S2A_END  = 120    # Green reaches 90° — aimed at Blue
F_S2_END   = 160    # HRG reaches 90° — system complete, Green on Blue
F_SWAP     = 161    # Ball transfers Green → Blue
F_RET1_END = 200    # HRG + Green back to 0°  (LIFO: last-in first-out)
F_RET2_END = 240    # HBR back to 0°           (LIFO: first-in last-out)
F_END      = 240

# Stage 1: HBR opens Blue 180° — mirror of HGY opening Yellow in T03
HBR_AXIS   = 0       # X
HBR_SIGN   = +1.0   # same as HGY_SIGN in T03
HBR_DEG    = 180.0

# Stage 2a: Cube_Green rotates 90° toward Blue — mirror of Cube_Red in T03
GREEN_AXIS = 1       # Y
GREEN_SIGN = +1.0   # mirrored from RED_SIGN=-1.0 in T03
GREEN_DEG  = 90.0

# Stage 2b: HRG swings whole system 90° — mirror of HRG in T03
HRG_AXIS   = 1       # Y
HRG_SIGN   = +1.0   # mirrored from HRG_SIGN=-1.0 in T03
HRG_DEG    = 90.0

# Ball starts inside Green (canonical world position)
BALL_GREEN_INTERIOR  = mathutils.Vector((-0.51, -0.51, 0.25))
# Blue destination side hole — mirrored from SEAT_YELLOW_SIDE_WORLD in T03
SEAT_BLUE_SIDE_WORLD = mathutils.Vector(( 0.51, -0.51, 0.25))

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

    # Flush depsgraph BEFORE clearing parents so world transforms are stable
    bpy.context.view_layer.update()

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
            obj.scale          = (1.0, 1.0, 1.0)

    for seat_name in ["Seat_Green_Start", "Seat_Blue_Side",
                      "Seat_Green", "Seat_Blue", "Seat_Red", "Seat_Yellow"]:
        obj = bpy.data.objects.get(seat_name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.context.view_layer.update()
    print("=== T4 reset to canonical ===")

###############################################################################
# SECTION 3: Helpers
###############################################################################

def _fcurves(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return []
    act = obj.animation_data.action
    try:
        return act.fcurves
    except AttributeError:
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
    print("=== T4 Start: Green → Blue ===")
    reset_scene_to_canonical()

    blue     = bpy.data.objects.get("Cube_Blue")
    red      = bpy.data.objects.get("Cube_Red")
    green    = bpy.data.objects.get("Cube_Green")
    yellow   = bpy.data.objects.get("Cube_Yellow")
    ball     = bpy.data.objects.get("Ball")
    hinge_br = bpy.data.objects.get("Hinge_Blue_Red")
    hinge_rg = bpy.data.objects.get("Hinge_Red_Green")
    hinge_gy = bpy.data.objects.get("Hinge_Green_Yellow")

    missing = [n for n, o in [
        ("Cube_Blue", blue), ("Cube_Red", red), ("Cube_Green", green),
        ("Cube_Yellow", yellow), ("Ball", ball),
        ("Hinge_Blue_Red", hinge_br), ("Hinge_Red_Green", hinge_rg),
        ("Hinge_Green_Yellow", hinge_gy),
    ] if o is None]
    if missing:
        print("ERROR: Missing:", missing)
        return False

    # ── Zero hinges ──────────────────────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    for h in (hinge_gy, hinge_rg, hinge_br):
        h.rotation_mode  = 'XYZ'
        h.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # ── Build hierarchy — HRG is world root (mirrors T03 exactly) ────────────
    # Local offsets = world_child − world_parent at canonical, all rotations zero.
    #
    # T03:  HRG → Green(-0.51,0.51,0) → HGY(0,0,0) → Yellow(0,0,0)
    #       HRG → HBR(0.51,0.51,0) → Red(-0.51,-0.51,0) → Blue(0.51,0.51,0)
    #
    # T04:  HRG → HGY(-0.51,0.51,0) → Green(0,0,0) → Yellow(0,0,0)   [src branch]
    #       HRG → Red(0,0,0) → HBR(0.51,0.51,0) → Blue(0,0,0)         [dest branch]
    I4 = mathutils.Matrix.Identity(4)

    def attach(child, parent, local_xyz):
        child.parent                = parent
        child.matrix_parent_inverse = I4.copy()
        child.location              = local_xyz
        child.rotation_euler        = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

    # Source branch: HRG → HGY → Green → Yellow
    attach(hinge_gy, hinge_rg, (-0.51,  0.51, 0.0))  # HGY local from HRG
    attach(green,    hinge_gy, ( 0.0,   0.0,  0.0))  # Green at HGY origin
    attach(yellow,   green,    ( 0.0,   0.0,  0.0))  # Yellow passive rider

    # Destination branch: HRG → Red → HBR → Blue
    attach(red,      hinge_rg, ( 0.0,   0.0,  0.0))  # Red at HRG origin (passive bridge)
    attach(hinge_br, red,      ( 0.51,  0.51, 0.0))  # HBR local from Red
    attach(blue,     hinge_br, ( 0.0,   0.0,  0.0))  # Blue at HBR origin (destination)

    print("Hierarchy: HRG(root) → [HGY→Green→Yellow] + [Red→HBR→Blue]")

    # ── Remove rigid body from ball ──────────────────────────────────────────
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    # ── Place ball inside Green ───────────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    ball.location = BALL_GREEN_INTERIOR.copy()
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()

    # ── Seats ────────────────────────────────────────────────────────────────
    ball_world = ball.matrix_world.translation.copy()

    seat_green_start = bpy.data.objects.new("Seat_Green_Start", None)
    seat_green_start.empty_display_type = 'SPHERE'
    seat_green_start.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_green_start)
    seat_green_start.parent   = green
    seat_green_start.location = green.matrix_world.inverted() @ ball_world

    seat_blue_side = bpy.data.objects.new("Seat_Blue_Side", None)
    seat_blue_side.empty_display_type = 'SPHERE'
    seat_blue_side.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue_side)
    seat_blue_side.parent   = blue
    seat_blue_side.location = blue.matrix_world.inverted() @ SEAT_BLUE_SIDE_WORLD

    bpy.context.view_layer.update()

    # ── Ball constraints ─────────────────────────────────────────────────────
    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name   = "Latch_Green_Start"
    latch_green.target = seat_green_start

    latch_blue = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_blue.name   = "Latch_Blue_Side"
    latch_blue.target = seat_blue_side

    # ── Stage 1 — HBR 0°→180° (Blue opens) ──────────────────────────────────
    # Mirrors T03 Stage 1: HGY 0°→180° (Yellow opened)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_START,    0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S1_END,   HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S2_END,   HBR_DEG)   # hold through 2a+2b
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_SWAP,     HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET1_END, HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET2_END, 0)

    # ── Stage 2a — Green 0°→90° (Cube_Green rotates toward Blue) ─────────────
    # Mirrors T03 Stage 2a: Red 0°→90° (Cube_Red rotated toward Yellow)
    key_rot(green, GREEN_AXIS, GREEN_SIGN, F_START,    0)
    key_rot(green, GREEN_AXIS, GREEN_SIGN, F_S1_END,   0)          # hold during Stage 1
    key_rot(green, GREEN_AXIS, GREEN_SIGN, F_S2A_END,  GREEN_DEG)
    key_rot(green, GREEN_AXIS, GREEN_SIGN, F_SWAP,     GREEN_DEG)
    key_rot(green, GREEN_AXIS, GREEN_SIGN, F_RET1_END, 0)
    key_rot(green, GREEN_AXIS, GREEN_SIGN, F_RET2_END, 0)

    # ── Stage 2b — HRG 0°→90° (whole system — Green lands on Blue) ───────────
    # Mirrors T03 Stage 2b: HRG 0°→90° (Red landed on Yellow)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_START,    0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S1_END,   0)          # hold during Stage 1
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2A_END,  0)          # hold during Stage 2a
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2_END,   HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_SWAP,     HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET1_END, 0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET2_END, 0)

    # ── Ball transfer at frame 161 ────────────────────────────────────────────
    key_influence(ball, "Latch_Green_Start", F_START,   1.0)
    key_influence(ball, "Latch_Blue_Side",   F_START,   0.0)
    key_influence(ball, "Latch_Green_Start", F_S2_END,  1.0)
    key_influence(ball, "Latch_Blue_Side",   F_S2_END,  0.0)
    key_influence(ball, "Latch_Green_Start", F_SWAP,    0.0)
    key_influence(ball, "Latch_Blue_Side",   F_SWAP,    1.0)
    key_influence(ball, "Latch_Green_Start", F_END,     0.0)
    key_influence(ball, "Latch_Blue_Side",   F_END,     1.0)

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== T4 Complete: Green → Blue ===")
    print(f"Stage 1  ({F_START:3d}–{F_S1_END:3d}): HBR  180° — Blue opens   [mirror HGY T03]")
    print(f"Stage 2a ({F_S1_END+1:3d}–{F_S2A_END:3d}): Green  90° — Green aims  [mirror Red T03]")
    print(f"Stage 2b ({F_S2A_END+1:3d}–{F_S2_END:3d}): HRG   90° — whole system [mirror HRG T03]")
    print(f"Frame {F_SWAP}: ball transfers Green→Blue")
    print(f"Return  ({F_SWAP+1:3d}–{F_RET1_END:3d}): HRG + Green back to 0°  (LIFO)")
    print(f"Return  ({F_RET1_END+1:3d}–{F_RET2_END:3d}): HBR back to 0°          (LIFO)")
    return True

###############################################################################
# SECTION 5: UI Panel
###############################################################################

class LORQB_OT_reset_t4(bpy.types.Operator):
    bl_idname      = "lorqb.reset_t4"
    bl_label       = "Reset to Base"
    bl_description = "Reset all objects to canonical state"

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "T4 reset to base")
        return {'FINISHED'}

class LORQB_OT_run_t4(bpy.types.Operator):
    bl_idname      = "lorqb.run_t4"
    bl_label       = "Run T4: Green → Blue"
    bl_description = "Arm T4: HBR opens Blue, Green rotates, HRG swings — ball drops Green→Blue"

    def execute(self, context):
        result = run_animation()
        if result:
            self.report({'INFO'}, "T4 armed — press Play to run")
        else:
            self.report({'ERROR'}, "T4 failed — check console")
        return {'FINISHED'}

class LORQB_PT_t4_panel(bpy.types.Panel):
    bl_label       = "LorQB — T4"
    bl_idname      = "LORQB_PT_t4_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_t4", text="Reset to Base",        icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.run_t4",   text="Run T4: Green → Blue", icon='PLAY')

_classes = [LORQB_OT_reset_t4, LORQB_OT_run_t4, LORQB_PT_t4_panel]

###############################################################################
# SECTION 6: Register / Entry Point
###############################################################################

def register():
    for name in ["LORQB_PT_t4_panel", "LORQB_OT_run_t4", "LORQB_OT_reset_t4"]:
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
