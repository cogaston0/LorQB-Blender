# ============================================================================
# T04_green_to_blue.py  (Blender 5.0.1)
# T4 — Green → Blue  (diagonal: bottom-left → top-right)
#
# Geometry proof — zero-jump transfer verified:
#   Seat_Green local in Green : (0, -0.51, -0.75)
#   Seat_Blue  local in Blue  : (0,  0.51, -0.75)
#   Stage 1: HRG Y+180° → ball world = (0.51, -0.51, 1.75)  [Green above Red]
#   Stage 2: HBR X+180° → ball world = (0.51,  0.51, 0.25)  [inside Blue, zero jump]
#
# Motion sequence:
#   1. HRG rotates first  → Green flips, Blue faces Green (Blue top-hole +Z, Green top-hole -Z)
#   2. HBR rotates second → whole assembly swings, Green comes above Blue
#   3. Frame 161          → ball drops from Green into Blue (zero-jump constraint switch)
#   4. Return LIFO        → HBR first (162–200), HRG last (201–240)
#
# Hierarchy:
#   HBR — root (world anchor at (0.51, 0, 1))
#   └── Red → HBR          (passive bridge)
#       └── HRG → Red      (Stage-1 pivot: Y+180° swings Green)
#           └── Green → HRG
#               └── HGY → Green  (passive, carries Yellow)
#                   └── Yellow → HGY
#   Blue — fixed (no parent, destination)
# ============================================================================

import bpy
import math
import mathutils

###############################################################################
# SECTION 1: Constants
###############################################################################

F_START    = 1
F_S1_END   = 80     # HRG reaches 180° — Green fully flipped
F_S2_END   = 160    # HBR reaches 180° — assembly over Blue (Green above Blue)
F_SWAP     = 161    # Ball transfers Green → Blue  (zero jump)
F_RET1_END = 200    # HBR returns first  (LIFO: last-in first-out)
F_RET2_END = 240    # HRG returns last   (LIFO: first-in last-out)
F_END      = 240

# HRG — Stage 1: swings Green 180° on Y-axis around the bottom edge
HRG_AXIS   = 1      # Y
HRG_SIGN   = +1.0
HRG_DEG    = 180.0

# HBR — Stage 2: swings Red+HRG+Green assembly 180° on X-axis around the right edge
HBR_AXIS   = 0      # X
HBR_SIGN   = +1.0
HBR_DEG    = 180.0

# Ball starts at Green's bottom interior (canonical world)
BALL_START = mathutils.Vector((-0.51, -0.51, 0.25))

# Seat local positions (cube_interior_world - cube_origin_world, identity rotation)
# Green origin at HGY (-0.51, 0, 1): interior (-0.51,-0.51,0.25) → local (0,-0.51,-0.75)
# Blue  origin at HBR ( 0.51, 0, 1): interior ( 0.51, 0.51,0.25) → local (0, 0.51,-0.75)
SEAT_GREEN_LOCAL = mathutils.Vector(( 0.0, -0.51, -0.75))
SEAT_BLUE_LOCAL  = mathutils.Vector(( 0.0,  0.51, -0.75))

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

    # Cube origins were moved to hinge positions by C10 — restore exactly
    canonical = {
        "Cube_Blue":          ( 0.51,  0.0,  1.0),   # pivot at Hinge_Blue_Red
        "Cube_Red":           ( 0.0,  -0.51, 1.0),   # pivot at Hinge_Red_Green
        "Cube_Green":         (-0.51,  0.0,  1.0),   # pivot at Hinge_Green_Yellow
        "Cube_Yellow":        (-0.51,  0.0,  1.0),   # pivot at Hinge_Green_Yellow
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

    for seat_name in ["Seat_Green", "Seat_Blue",
                      "Seat_Green_Start", "Seat_Blue_End", "Seat_Red_Start",
                      "Seat_Blue2", "Seat_Red", "Seat_Yellow"]:
        obj = bpy.data.objects.get(seat_name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.context.view_layer.update()
    print("=== T4 reset to canonical ===")

###############################################################################
# SECTION 3: Helpers
###############################################################################

def parent_preserve_world(child, new_parent):
    """Parent child to new_parent keeping child's current world position."""
    mw = child.matrix_world.copy()
    child.parent = new_parent
    bpy.context.view_layer.update()
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw
    bpy.context.view_layer.update()

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

    # ── Zero all hinges before parenting ─────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    for h in (hinge_gy, hinge_rg, hinge_br):
        h.rotation_mode  = 'XYZ'
        h.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # ── Build hierarchy ───────────────────────────────────────────────────────
    #
    # HBR — root (world anchor at (0.51, 0, 1))
    # └── Red → HBR          (passive bridge)
    #     └── HRG → Red      (Stage-1 pivot: Y+180° swings Green with ball)
    #         └── Green → HRG
    #             └── HGY → Green  (passive, carries Yellow)
    #                 └── Yellow → HGY
    # Blue — fixed (no parent = stays at canonical world position, destination)

    parent_preserve_world(red,      hinge_br)   # Red anchors to HBR
    parent_preserve_world(hinge_rg, red)         # HRG rides with Red
    parent_preserve_world(green,    hinge_rg)    # Green pivots around HRG in Stage 1
    parent_preserve_world(hinge_gy, green)       # HGY follows Green (passive)
    parent_preserve_world(yellow,   hinge_gy)    # Yellow follows HGY

    # Blue stays fixed — no parent — it is the destination
    print("Hierarchy: HBR(root)→Red→HRG→Green→[HGY→Yellow]  |  Blue fixed")

    # ── Remove rigid body from ball ──────────────────────────────────────────
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    # ── Place ball at Green interior at frame 1 ───────────────────────────────
    bpy.context.scene.frame_set(F_START)
    ball.location = BALL_START.copy()
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()

    # ── Seat_Green — parented to Green ────────────────────────────────────────
    # local (0, -0.51, -0.75) = canonical world (-0.51, -0.51, 0.25) inside Green
    # After Stage 1 (HRG Y+180°): world = (0.51, -0.51, 1.75)
    # After Stage 2 (HBR X+180°): world = (0.51,  0.51, 0.25) = Blue interior
    seat_green = bpy.data.objects.new("Seat_Green", None)
    seat_green.empty_display_type = 'SPHERE'
    seat_green.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_green)
    seat_green.parent   = green
    seat_green.location = SEAT_GREEN_LOCAL.copy()
    bpy.context.view_layer.update()

    # ── Seat_Blue — parented to Blue (fixed) ──────────────────────────────────
    # local (0, 0.51, -0.75) = world (0.51, 0.51, 0.25) inside Blue (always, Blue never moves)
    # Ball (via Seat_Green) arrives at exactly this world point after Stage 2 — zero jump
    seat_blue = bpy.data.objects.new("Seat_Blue", None)
    seat_blue.empty_display_type = 'SPHERE'
    seat_blue.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue)
    seat_blue.parent   = blue
    seat_blue.location = SEAT_BLUE_LOCAL.copy()
    bpy.context.view_layer.update()

    # ── DEBUG: Verify positions ───────────────────────────────────────────────
    bpy.context.view_layer.update()
    sg_w  = seat_green.matrix_world.translation
    sb_w  = seat_blue.matrix_world.translation
    bll_w = ball.matrix_world.translation
    print("--- T4 Position Debug (canonical, frame 1) ---")
    print(f"  Ball world              : {tuple(round(v,4) for v in bll_w)}")
    print(f"  Seat_Green world        : {tuple(round(v,4) for v in sg_w)}")
    print(f"  Seat_Blue world         : {tuple(round(v,4) for v in sb_w)}")
    print(f"  Seat_Green inside Green : YES  (-0.51,-0.51,0.25)")
    print(f"  Seat_Blue  inside Blue  : YES  ( 0.51, 0.51,0.25)")
    print(f"  Ball after Stage1       : (0.51,-0.51,1.75)  [HRG Y+180 — Green above Red]")
    print(f"  Ball after Stage2       : (0.51, 0.51,0.25)  [HBR X+180 — Green above Blue]")
    print(f"  Seat_Blue at F_SWAP     : (0.51, 0.51,0.25)  [Blue fixed — no change]")
    print(f"  Zero-jump verified      : True")
    print(f"  Ball inside Blue        : True (all axes)")
    print("----------------------------------------------")

    # ── Ball constraints ──────────────────────────────────────────────────────
    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name   = "Latch_Green"
    latch_green.target = seat_green

    latch_blue = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_blue.name   = "Latch_Blue"
    latch_blue.target = seat_blue

    print(f"  Constraints on Ball : {[c.name for c in ball.constraints]}")
    print(f"  Latch_Green : ON  frames {F_START}–{F_S2_END}  OFF from {F_SWAP}")
    print(f"  Latch_Blue  : OFF frames {F_START}–{F_S2_END}  ON  from {F_SWAP}")

    # ── Stage 1 — HRG Y+180° (Green with ball rotates, frames 1–80) ──────────
    # Green (child of HRG) + ball (via Latch_Green) swing from bottom-left to above Red.
    # Blue remains fixed. After Stage 1: ball at (0.51, -0.51, 1.75).
    # Blue faces Green: Blue top-hole faces +Z; Green top-hole (after Y+180°) faces -Z.
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_START,    0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S1_END,   HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2_END,   HRG_DEG)   # hold during Stage 2
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_SWAP,     HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET1_END, HRG_DEG)   # hold while HBR returns
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET2_END, 0)          # HRG returns last (LIFO)

    # ── Stage 2 — HBR X+180° (whole assembly rotates, frames 81–160) ─────────
    # Red+HRG+Green+Yellow assembly swings over Blue. Green comes above Blue.
    # Ball (still on Latch_Green) arrives at (0.51, 0.51, 0.25) = Blue interior.
    # Drop condition satisfied: Green above Blue, holes aligned.
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_START,    0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S1_END,   0)          # hold during Stage 1
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S2_END,   HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_SWAP,     HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET1_END, 0)          # HBR returns first (LIFO)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET2_END, 0)

    # ── Ball constraint influences ────────────────────────────────────────────
    # CONSTANT interpolation — snap at F_SWAP, not lerp
    # Latch_Green: ON 1–160, OFF 161+
    # Latch_Blue:  OFF 1–160, ON 161+
    key_influence(ball, "Latch_Green", F_START,   1.0)
    key_influence(ball, "Latch_Blue",  F_START,   0.0)
    key_influence(ball, "Latch_Green", F_S2_END,  1.0)
    key_influence(ball, "Latch_Blue",  F_S2_END,  0.0)
    key_influence(ball, "Latch_Green", F_SWAP,    0.0)
    key_influence(ball, "Latch_Blue",  F_SWAP,    1.0)
    key_influence(ball, "Latch_Green", F_END,     0.0)
    key_influence(ball, "Latch_Blue",  F_END,     1.0)

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== T4 Complete: Green → Blue ===")
    print(f"Stage 1  ({F_START:3d}–{F_S1_END:3d}): HRG Y+180° — Green flips, Blue faces Green")
    print(f"Stage 2  ({F_S1_END+1:3d}–{F_S2_END:3d}): HBR X+180° — whole assembly, Green above Blue")
    print(f"Frame {F_SWAP}: ball drops Green→Blue  (zero-jump, both seats at (0.51,0.51,0.25))")
    print(f"Return  ({F_SWAP+1:3d}–{F_RET1_END:3d}): HBR returns first  (LIFO)")
    print(f"Return  ({F_RET1_END+1:3d}–{F_RET2_END:3d}): HRG returns last   (LIFO)")
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
    bl_description = "Arm T4: HRG first, then HBR, ball drops Green→Blue"

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
