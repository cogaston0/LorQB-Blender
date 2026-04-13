# ============================================================================
# T04_green_to_blue.py  (Blender 5.0.1)
# T4 — Green → Blue
#
# Structural-fix build (not a sign-flipped copy of T03):
#   Green is rotated around an HRG-anchored pivot empty (Pivot_Green_HRG),
#   NOT around its own origin at HGY. This keeps the Green/Red shared
#   hinge edge coincident at all frames — no detachment.
#   HBR owns Blue opening directly in Stage 1.
#
# Three moves, no detachment:
#   Stage 1  (  1– 80): HBR X ±180°     — Blue opens (sign verified at runtime)
#   Stage 2a ( 81–120): Pivot_Green_HRG Y +90° — Green sweeps around HRG toward Blue
#   Stage 2b (121–160): HRG Y −90°      — whole system rotates, Green lands on Blue
#   Frame 161:          Ball transfers Green → Blue
#   Return   (162–200): HRG + Pivot_Green_HRG back to 0°
#   Return   (201–240): HBR back to 0°
#
# No detachment guarantee:
#   HRG is the world root. Every cube, hinge, and pivot is a child.
#   Rotations move the tree — no child is ever unparented mid-animation.
#   Green rides on Pivot_Green_HRG whose center is HRG, so the Green/Red
#   hinge edge stays coincident throughout Stage 2a.
#
# Hierarchy:
#   HRG (root)
#   ├── Red → HBR → Blue                        (Blue side)
#   └── Pivot_Green_HRG → Green → HGY → Yellow  (Green side, HRG-pivoted)
# ============================================================================

import bpy
import math
import mathutils

###############################################################################
# SECTION 1: Constants
###############################################################################

F_START    = 1
F_S1_END   = 80     # HBR reaches -180°
F_S2A_END  = 120    # Green reaches +90°
F_S2_END   = 160    # HRG reaches -90° — system complete
F_SWAP     = 161    # Ball transfers Green → Blue
F_RET1_END = 200    # HRG + Green back to 0°
F_RET2_END = 240    # HBR back to 0°
F_END      = 240

# Stage 1 — HBR opens Blue. Sign to be verified at runtime after hierarchy
# fix (per Rukmini directive item 7). Start with −1; invert to +1 if Blue
# opens downward in test.
HBR_AXIS   = 0       # X
HBR_SIGN   = -1.0
HBR_DEG    = 180.0

# Stage 2a — Green: mirror of T03 Red (Y+90°). Y sign unchanged → Y+90°.
GREEN_AXIS = 1       # Y
GREEN_SIGN = +1.0
GREEN_DEG  = 90.0

# Stage 2b — HRG: mirror of T03 HRG (Y−90°). Y sign unchanged → Y−90°.
HRG_AXIS   = 1       # Y
HRG_SIGN   = -1.0
HRG_DEG    = 90.0

# Ball world positions — Y-mirror of T03
# T03:  BALL_RED_INTERIOR      = ( 0.51, -0.51, 0.25)
# T04:  mirror Y-axis          = (-0.51, -0.51, 0.25)   inside Green
BALL_GREEN_INTERIOR = mathutils.Vector((-0.51, -0.51, 0.25))

# T03:  SEAT_YELLOW_SIDE_WORLD = (-0.51,  0.51, 0.25)
# T04:  mirror Y-axis          = ( 0.51,  0.51, 0.25)   inside Blue
SEAT_BLUE_SIDE_WORLD = mathutils.Vector(( 0.51,  0.51, 0.25))

###############################################################################
# SECTION 2: Reset
###############################################################################

def reset_scene_to_canonical():
    for name in ["Ball",
                 "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
                 "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
                 "Pivot_Green_HRG"]:
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

    # Explicit HRG stale-parent guard — a prior T-script may leave HRG
    # with a parent, causing wrong world positions after attach().
    hinge_rg = bpy.data.objects.get("Hinge_Red_Green")
    if hinge_rg:
        hinge_rg.parent = None
        bpy.context.view_layer.update()
        hinge_rg.location = (0.0, -0.51, 1.0)

    canonical = {
        "Cube_Blue":          ( 0.51,  0.0,  1.0),   # origin at HBR
        "Cube_Red":           ( 0.0,  -0.51, 1.0),   # origin at HRG
        "Cube_Green":         (-0.51,  0.0,  1.0),   # origin at HGY
        "Cube_Yellow":        (-0.51,  0.0,  1.0),   # origin at HGY
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

    # Remove any T4-created helpers so a re-run starts clean
    for helper_name in ["Seat_Green_Start", "Seat_Blue_Side", "Pivot_Green_HRG"]:
        obj = bpy.data.objects.get(helper_name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.context.view_layer.update()
    print("=== T4 reset to canonical ===")

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

    try:
        if action.fcurves:
            fcurves = action.fcurves
    except AttributeError:
        pass

    if fcurves is None:
        try:
            slot = action.slots[0]
            strip = action.layers[0].strips[0]
            bag = strip.channelbag_for_slot(slot)
            if bag is not None:
                fcurves = bag.fcurves
        except Exception:
            pass

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

    # ── Build hierarchy — HRG is world root ──────────────────────────────────
    # Structural fix (Rukmini directive):
    #   Green must NOT rotate from HGY ownership.
    #   Green stays attached to Red-side structure through HRG at all times.
    #   Stage 2a is driven by an HRG-based pivot empty (Pivot_Green_HRG),
    #   NOT by rotating Cube_Green around its own origin at HGY.
    #   HBR owns Blue opening directly in Stage 1.
    I4 = mathutils.Matrix.Identity(4)

    def attach(child, parent, local_xyz):
        child.parent                = parent
        child.matrix_parent_inverse = I4.copy()
        child.location              = mathutils.Vector(local_xyz)
        child.rotation_euler        = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

    # Locked canonical world positions (from CLAUDE.md layout lock):
    #   Hinge_Blue_Red     = ( 0.51,  0.0, 1.0)
    #   Hinge_Red_Green    = ( 0.0,  -0.51, 1.0)
    #   Hinge_Green_Yellow = (-0.51,  0.0, 1.0)
    #   Cube_Red           = ( 0.0,  -0.51, 1.0)  (at HRG)
    #   Cube_Blue          = ( 0.51,  0.0,  1.0)  (at HBR)
    #   Cube_Green         = (-0.51,  0.0,  1.0)  (at HGY)
    #   Cube_Yellow        = (-0.51,  0.0,  1.0)  (at HGY)

    # Branch 1 (Blue side): HRG → Red → HBR → Blue
    #   Red is the passive bridge from HRG to the Blue subtree.
    #   HBR owns Blue so HBR rotation in Stage 1 opens Blue directly.
    # Red world = (0, -0.51, 1), HRG world = (0, -0.51, 1) → local (0,0,0)
    attach(red,      hinge_rg, ( 0.0,   0.0,  0.0))
    # HBR world = (0.51, 0, 1); Red world = (0, -0.51, 1) → local (0.51, 0.51, 0)
    attach(hinge_br, red,      ( 0.51,  0.51, 0.0))
    # Blue world = (0.51, 0, 1); HBR world = (0.51, 0, 1) → local (0, 0, 0)
    attach(blue,     hinge_br, ( 0.0,   0.0,  0.0))

    # Branch 2 (Green side): HRG → Pivot_Green_HRG → Cube_Green → HGY → Yellow
    #   Pivot_Green_HRG is an empty at HRG's world position, child of HRG,
    #   giving Stage 2a a rotation center at the HRG hinge — so Green sweeps
    #   around HRG (shared Red/Green edge) instead of around its own origin.
    #   This keeps the Green/Red shared hinge edge coincident at all frames.
    pivot_green = bpy.data.objects.get("Pivot_Green_HRG")
    if pivot_green is None:
        pivot_green = bpy.data.objects.new("Pivot_Green_HRG", None)
        pivot_green.empty_display_type = 'PLAIN_AXES'
        pivot_green.empty_display_size = 0.15
        bpy.context.scene.collection.objects.link(pivot_green)

    # Pivot empty sits at HRG (local 0,0,0 under hinge_rg → world = HRG world)
    attach(pivot_green, hinge_rg, ( 0.0,   0.0,  0.0))
    # Green world = (-0.51, 0, 1); pivot world = (0, -0.51, 1) → local (-0.51, 0.51, 0)
    attach(green,       pivot_green, (-0.51, 0.51, 0.0))
    # HGY world = (-0.51, 0, 1); Green world = (-0.51, 0, 1) → local (0, 0, 0)
    attach(hinge_gy,    green,       ( 0.0,  0.0,  0.0))
    # Yellow world = (-0.51, 0, 1); HGY world = (-0.51, 0, 1) → local (0, 0, 0)
    attach(yellow,      hinge_gy,    ( 0.0,  0.0,  0.0))

    print("Hierarchy: HRG(root) → [Red→HBR→Blue] + [Pivot_Green_HRG→Green→HGY→Yellow]")

    # World-position verification after hierarchy build
    bpy.context.view_layer.update()
    _verify = {
        "Cube_Red":           ( 0.0,  -0.51, 1.0),
        "Hinge_Blue_Red":     ( 0.51,  0.0,  1.0),
        "Cube_Blue":          ( 0.51,  0.0,  1.0),
        "Pivot_Green_HRG":    ( 0.0,  -0.51, 1.0),
        "Cube_Green":         (-0.51,  0.0,  1.0),
        "Hinge_Green_Yellow": (-0.51,  0.0,  1.0),
        "Cube_Yellow":        (-0.51,  0.0,  1.0),
    }
    print("=== T4 Hierarchy World-Position Verification ===")
    all_ok = True
    for _name, _expected in _verify.items():
        _obj = bpy.data.objects.get(_name)
        if _obj:
            _actual = tuple(round(v, 3) for v in _obj.matrix_world.translation)
            _ok = all(abs(_actual[i] - _expected[i]) < 0.02 for i in range(3))
            if not _ok:
                all_ok = False
            print(f"  {'OK    ' if _ok else 'DETACH'} {_name}: actual={_actual}  expected={_expected}")
    if not all_ok:
        print("ERROR: Hierarchy verification failed — aborting T4")
        return False

    # ── Remove rigid body from ball ──────────────────────────────────────────
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    # ── Place ball inside Green ──────────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    ball.location = BALL_GREEN_INTERIOR.copy()
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()

    # ── Seats (parented to source/dest cubes, mirror of T03) ─────────────────
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

    # ── Stage 1 — HBR X −180° (Blue opens) ──────────────────────────────────
    # Mirror of T03 Stage 1 (HGY X+180°). X sign flipped.
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_START,    0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S1_END,   HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S2_END,   HBR_DEG)   # hold through 2a+2b
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_SWAP,     HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET1_END, HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET2_END, 0)

    # ── Stage 2a — Pivot_Green_HRG Y +90° (Green sweeps around HRG) ─────────
    # Green is rotated via an HRG-anchored pivot empty, NOT by rotating
    # Cube_Green on its own origin. This preserves the Green/Red shared
    # hinge edge at all frames (no detachment).
    pivot_green_obj = bpy.data.objects.get("Pivot_Green_HRG")
    key_rot(pivot_green_obj, GREEN_AXIS, GREEN_SIGN, F_START,    0)
    key_rot(pivot_green_obj, GREEN_AXIS, GREEN_SIGN, F_S1_END,   0)          # hold during Stage 1
    key_rot(pivot_green_obj, GREEN_AXIS, GREEN_SIGN, F_S2A_END,  GREEN_DEG)
    key_rot(pivot_green_obj, GREEN_AXIS, GREEN_SIGN, F_SWAP,     GREEN_DEG)
    key_rot(pivot_green_obj, GREEN_AXIS, GREEN_SIGN, F_RET1_END, 0)
    key_rot(pivot_green_obj, GREEN_AXIS, GREEN_SIGN, F_RET2_END, 0)

    # ── Stage 2b — HRG Y −90° (whole system) ────────────────────────────────
    # Mirror of T03 Stage 2b (HRG Y−90°). Y sign unchanged — identical to T03.
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_START,    0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S1_END,   0)          # hold during Stage 1
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2A_END,  0)          # hold during Stage 2a
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2_END,   HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_SWAP,     HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET1_END, 0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET2_END, 0)

    # ── Ball transfer at frame 161 ───────────────────────────────────────────
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
    print(f"Stage 1  (1–80):    HBR X {HBR_SIGN:+.0f}*{HBR_DEG:.0f}° — Blue opens (VERIFY SIGN)")
    print("Stage 2a (81–120):  Pivot_Green_HRG Y+90° — Green sweeps around HRG")
    print("Stage 2b (121–160): HRG Y−90°  — whole system")
    print("Frame 161: ball transfers Green → Blue")
    print("Return  (162–200): HRG + Pivot_Green_HRG → 0°")
    print("Return  (201–240): HBR → 0°")
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
    bl_description = "Arm T4 animation: Green transfers ball to Blue"

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
        layout.operator("lorqb.reset_t4", text="Reset to Base", icon='LOOP_BACK')
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
