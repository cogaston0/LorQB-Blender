# ============================================================================
# T03_red_to_yellow.py  (Blender 5.0.1)
# T3 — Red → Yellow
#
# Three moves, no detachment:
#   Stage 1  (  1– 80): HGY 180° — Yellow opens side hole toward Red
#   Stage 2a ( 81–120): Red 90°  — Cube_Red rotates directly toward Yellow
#   Stage 2b (121–160): HRG  90° — whole system rotates, Red lands on Yellow
#   Frame 161:          Ball transfers Red → Yellow
#   Return   (162–200): HRG + Red back to 0°
#   Return   (201–240): HGY back to 0°
#
# No detachment guarantee:
#   HRG is the world root. Every cube and hinge is a child.
#   Rotations move the tree — no child is ever unparented mid-animation.
#
# Hierarchy:
#   HRG (root)
#   ├── Green → HGY → Yellow
#   └── HBR  → Red  → Blue
# ============================================================================

import bpy
import math
import mathutils

###############################################################################
# SECTION 1: Constants
###############################################################################

F_START    = 1
F_S1_END   = 80     # HGY reaches 180°
F_S2A_END  = 120    # HBR reaches 90° — Red aimed at Yellow
F_S2_END   = 160    # HRG reaches 90° — system complete
F_SWAP     = 161    # Ball transfers Red → Yellow
F_RET1_END = 200    # HRG + HBR back to 0°
F_RET2_END = 240    # HGY back to 0°
F_END      = 240

HGY_AXIS   = 0
HGY_SIGN   = +1.0
HGY_DEG    = 180.0

RED_AXIS   = 1       # Y-axis — tips Red opening toward Yellow; flip sign if wrong
RED_SIGN   = -1.0
RED_DEG    = 90.0

HRG_AXIS   = 1       # Y-axis — confirmed correct direction
HRG_SIGN   = -1.0    # flipped from +1.0 per user 2026-04-22
HRG_DEG    = 90.0

BALL_RED_INTERIOR      = mathutils.Vector(( 0.51, -0.51, 0.25))
SEAT_YELLOW_SIDE_WORLD = mathutils.Vector((-0.51,  0.51, 0.25))

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

    # Fix 2: explicit HRG stale-parent guard — a prior T02 run may leave HRG
    # with a parent, causing wrong world positions for all children after attach().
    hinge_rg = bpy.data.objects.get("Hinge_Red_Green")
    if hinge_rg:
        hinge_rg.parent = None
        bpy.context.view_layer.update()
        hinge_rg.location = (0.0, -0.51, 1.0)

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

    for name in ["Seat_Red_Start", "Seat_Yellow_Side",
                 "Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.context.view_layer.update()
    print("=== T3 reset to canonical ===")

###############################################################################
# SECTION 3: Helpers
###############################################################################

def set_last_keyframe_interpolation(obj, data_path, frame, interp='LINEAR'):
    """Set interpolation on keyframes nearest `frame` on matching fcurves.
    Tries three accessors in order — covers Blender < 4.4 and 4.4+/5.x."""
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    fcurves = None

    # Accessor 1: legacy direct fcurves (Blender < 4.4, or compat mode)
    try:
        if action.fcurves:
            fcurves = action.fcurves
    except AttributeError:
        pass

    # Accessor 2: slotted API — strip.channelbag_for_slot(slot)  (Blender 4.4+/5.x)
    if fcurves is None:
        try:
            slot = action.slots[0]
            strip = action.layers[0].strips[0]
            bag = strip.channelbag_for_slot(slot)
            if bag is not None:
                fcurves = bag.fcurves
        except Exception:
            pass

    # Accessor 3: direct channelbags index fallback
    if fcurves is None:
        try:
            fcurves = action.layers[0].strips[0].channelbags[0].fcurves
        except Exception:
            pass

    if fcurves is None:
        print(f"WARNING: could not access fcurves on {obj.name} — interpolation not set")
        return

    for fc in fcurves:
        if data_path in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp

def key_rot(obj, axis, sign, frame, degrees, interp='LINEAR'):
    bpy.context.scene.frame_set(frame)
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler[axis] = sign * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=axis, frame=frame)
    set_last_keyframe_interpolation(obj, "rotation_euler", frame, interp)

def key_influence(obj, con_name, frame, value):
    bpy.context.scene.frame_set(frame)
    con = obj.constraints.get(con_name)
    if not con:
        print(f"WARNING: constraint '{con_name}' not found")
        return
    con.influence = value
    dp = f'constraints["{con_name}"].influence'
    obj.keyframe_insert(data_path=dp, frame=frame)
    set_last_keyframe_interpolation(obj, dp, frame, 'CONSTANT')

###############################################################################
# SECTION 4: Animation
###############################################################################

def run_animation():
    print("=== T3 Start: Red → Yellow ===")
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

    # ── Build hierarchy — HRG is world root ──────────────────────────────────
    I4 = mathutils.Matrix.Identity(4)

    def attach(child, parent, local_xyz):
        child.parent                = parent
        child.matrix_parent_inverse = I4.copy()
        child.location              = local_xyz
        child.rotation_euler        = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

    # Branch 1: Green → HGY → Yellow
    attach(green,    hinge_rg, (-0.51,  0.51, 0.0))
    attach(hinge_gy, green,    ( 0.0,   0.0,  0.0))
    attach(yellow,   hinge_gy, ( 0.0,   0.0,  0.0))

    # Branch 2: HBR → Red → Blue
    attach(hinge_br, hinge_rg, ( 0.51,  0.51, 0.0))
    attach(red,      hinge_br, (-0.51, -0.51, 0.0))
    attach(blue,     red,      ( 0.51,  0.51, 0.0))

    print("Hierarchy: HRG(root) → [Green→HGY→Yellow] + [HBR→Red→Blue]")

    # Fix 3: world-position verification after hierarchy build
    bpy.context.view_layer.update()
    _verify = {
        "Cube_Green":         (-0.51,  0.0,  1.0),
        "Hinge_Green_Yellow": (-0.51,  0.0,  1.0),
        "Cube_Yellow":        (-0.51,  0.51, 1.0),
        "Hinge_Blue_Red":     ( 0.51,  0.0,  1.0),
        "Cube_Red":           ( 0.0,  -0.51, 1.0),
        "Cube_Blue":          ( 0.51,  0.51, 1.0),
    }
    print("=== T3 Hierarchy World-Position Verification ===")
    for _name, _expected in _verify.items():
        _obj = bpy.data.objects.get(_name)
        if _obj:
            _actual = tuple(round(v, 3) for v in _obj.matrix_world.translation)
            _ok = all(abs(_actual[i] - _expected[i]) < 0.02 for i in range(3))
            print(f"  {'OK    ' if _ok else 'DETACH'} {_name}: actual={_actual}  expected={_expected}")

    # ── Remove rigid body from ball ──────────────────────────────────────────
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    # ── Place ball inside Red ────────────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    ball.location = BALL_RED_INTERIOR.copy()
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()

    # ── Seats ────────────────────────────────────────────────────────────────
    ball_world = ball.matrix_world.translation.copy()

    seat_red_start = bpy.data.objects.new("Seat_Red_Start", None)
    seat_red_start.empty_display_type = 'SPHERE'
    seat_red_start.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_red_start)
    seat_red_start.parent   = red
    seat_red_start.location = red.matrix_world.inverted() @ ball_world

    seat_yellow_side = bpy.data.objects.new("Seat_Yellow_Side", None)
    seat_yellow_side.empty_display_type = 'SPHERE'
    seat_yellow_side.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_yellow_side)
    seat_yellow_side.parent   = yellow
    seat_yellow_side.location = yellow.matrix_world.inverted() @ SEAT_YELLOW_SIDE_WORLD

    bpy.context.view_layer.update()

    # ── Ball constraints ─────────────────────────────────────────────────────
    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name   = "Latch_Red_Start"
    latch_red.target = seat_red_start

    latch_yellow = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_yellow.name   = "Latch_Yellow_Side"
    latch_yellow.target = seat_yellow_side

    # ── Stage 1 — HGY 0°→180° (Yellow opens) ────────────────────────────────
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_START,    0)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_S1_END,   HGY_DEG)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_S2_END,   HGY_DEG)   # hold through 2a+2b
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_SWAP,     HGY_DEG)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_RET1_END, HGY_DEG)
    key_rot(hinge_gy, HGY_AXIS, HGY_SIGN, F_RET2_END, 0)

    # ── Stage 2a — Red 0°→90° (Cube_Red rotates directly toward Yellow) ─────
    key_rot(red, RED_AXIS, RED_SIGN, F_START,    0)
    key_rot(red, RED_AXIS, RED_SIGN, F_S1_END,   0)                # hold during Stage 1
    key_rot(red, RED_AXIS, RED_SIGN, F_S2A_END,  RED_DEG)
    key_rot(red, RED_AXIS, RED_SIGN, F_SWAP,     RED_DEG)
    key_rot(red, RED_AXIS, RED_SIGN, F_RET1_END, 0)
    key_rot(red, RED_AXIS, RED_SIGN, F_RET2_END, 0)

    # ── Stage 2b — HRG 0°→90° (whole system — confirmed correct direction) ───
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_START,    0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S1_END,   0)          # hold during Stage 1
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2A_END,  0)          # hold during Stage 2a
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2_END,   HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_SWAP,     HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET1_END, 0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET2_END, 0)

    # ── Ball transfer at frame 161 ───────────────────────────────────────────
    key_influence(ball, "Latch_Red_Start",   F_START,   1.0)
    key_influence(ball, "Latch_Yellow_Side", F_START,   0.0)
    key_influence(ball, "Latch_Red_Start",   F_S2_END,  1.0)
    key_influence(ball, "Latch_Yellow_Side", F_S2_END,  0.0)
    key_influence(ball, "Latch_Red_Start",   F_SWAP,    0.0)
    key_influence(ball, "Latch_Yellow_Side", F_SWAP,    1.0)
    key_influence(ball, "Latch_Red_Start",   F_END,     0.0)
    key_influence(ball, "Latch_Yellow_Side", F_END,     1.0)

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== T3 Complete: Red → Yellow ===")
    print("Stage 1  (1–80):   HGY 180° — Yellow opens")
    print("Stage 2a (81–120):  Red  90° — Cube_Red rotates directly toward Yellow")
    print("Stage 2b (121–160): HRG  90° — whole system (confirmed correct)")
    print("Frame 161: ball transfers")
    print("T03 Fix applied: channelbag accessor + HRG stale parent guard + verify block.")
    return True

###############################################################################
# SECTION 5: UI Panel
###############################################################################

class LORQB_OT_reset_t3(bpy.types.Operator):
    bl_idname      = "lorqb.reset_t3"
    bl_label       = "Reset to Base"
    bl_description = "Reset all objects to canonical state"

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "T3 reset to base")
        return {'FINISHED'}

class LORQB_OT_run_t3(bpy.types.Operator):
    bl_idname      = "lorqb.run_t3"
    bl_label       = "Run T3: Red → Yellow"
    bl_description = "Arm T3 animation: Red transfers ball to Yellow"

    def execute(self, context):
        result = run_animation()
        if result:
            self.report({'INFO'}, "T3 armed — press Play to run")
        else:
            self.report({'ERROR'}, "T3 failed — check console")
        return {'FINISHED'}

class LORQB_PT_t3_panel(bpy.types.Panel):
    bl_label       = "LorQB — T3"
    bl_idname      = "LORQB_PT_t3_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_t3", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.run_t3",   text="Run T3: Red → Yellow", icon='PLAY')

_classes = [LORQB_OT_reset_t3, LORQB_OT_run_t3, LORQB_PT_t3_panel]

###############################################################################
# SECTION 6: Register / Entry Point
###############################################################################

def setup_red_to_yellow():
    return run_animation()

def register():
    for name in ["LORQB_OT_t3_stage1", "LORQB_OT_t3_stage2a", "LORQB_OT_t3_stage2b",
                 "LORQB_PT_t3_panel",  "LORQB_OT_run_t3",     "LORQB_OT_reset_t3"]:
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
