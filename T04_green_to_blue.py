# ============================================================================
# T04_green_to_blue.py  (Blender 5.0.1)
# T4 — Green → Blue
#
# System pivot: Pivot_System_T4 at world (0, 0, 1)
# Pivot rotates -90° on Y (frames 121–160) to position Green above Blue
#
# Parenting (constant, no re-parenting mid-animation):
#   Pivot_System_T4 (root)
#   ├── Hinge_Red_Green (HRG)
#   │   └── Cube_Green
#   │       └── Hinge_Green_Yellow → Cube_Yellow
#   └── Hinge_Blue_Red (HBR)
#       └── Cube_Red
#           └── Cube_Blue
#
# Animation:
#   Frames 1–80:     Hinge_Blue_Red +180°  (open Blue)
#   Frames 81–120:   Hinge_Red_Green +90°  (swing Green)
#   Frames 121–160:  Pivot_System_T4 −90° Y (system reposition)
#   Frame 161:       Ball transfers Green → Blue
#   Frames 162–200:  Pivot_System_T4 back to 0°, HRG back to 0°
#   Frames 201–240:  HBR back to 0°
# ============================================================================

import bpy
import math
import mathutils

###############################################################################
# SECTION 1: Constants
###############################################################################

PIVOT_NAME = "System_Rotator"
Z_HINGE    = 1.0

F_START    = 1
F_S1_END   = 80
F_S2A_END  = 120
F_S2B_END  = 160
F_SWAP     = 161
F_RET1_END = 200
F_RET2_END = 240
F_END      = 240

HBR_AXIS   = 0
HBR_SIGN   = +1.0
HBR_DEG    = 180.0

HRG_AXIS   = 1
HRG_SIGN   = -1.0
HRG_DEG    = 90.0

PIVOT_AXIS = 1
PIVOT_SIGN = -1.0
PIVOT_DEG  = 90.0

BALL_GREEN_INTERIOR     = mathutils.Vector((-0.51, -0.51, 0.25))
SEAT_BLUE_SIDE_WORLD    = mathutils.Vector(( 0.51, -0.51, 0.25))

###############################################################################
# SECTION 2: Reset
###############################################################################

def reset_scene_to_canonical():
    # Clear animation
    for name in ["Ball",
                 "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
                 "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    # Clear ball constraints
    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    # Clear animation on System_Rotator and zero its rotation — NEVER delete SR
    sr = bpy.data.objects.get(PIVOT_NAME)
    if sr:
        if sr.animation_data:
            sr.animation_data_clear()
        sr.rotation_mode  = 'XYZ'
        sr.rotation_euler = (0.0, 0.0, 0.0)

    # Zero hinges
    for name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        h = bpy.data.objects.get(name)
        if h:
            h.rotation_mode  = 'XYZ'
            h.rotation_euler = (0.0, 0.0, 0.0)

    bpy.context.view_layer.update()

    # Unparent all
    for name in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
                 "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        obj = bpy.data.objects.get(name)
        if obj and obj.parent:
            obj.parent = None

    bpy.context.view_layer.update()

    # Restore canonical positions (confirmed by user Q3)
    canonical = {
        "Cube_Blue":          ( 0.51,  0.51, 1.0),
        "Cube_Red":           ( 0.51, -0.51, 1.0),
        "Cube_Green":         (-0.51, -0.51, 1.0),
        "Cube_Yellow":        (-0.51,  0.51, 1.0),
        "Hinge_Blue_Red":     ( 0.51,  0.0,  1.0),
        "Hinge_Red_Green":    ( 0.0,  -0.51, 1.0),
        "Hinge_Green_Yellow": (-0.51,  0.0,  1.0),
    }
    for name, loc in canonical.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location       = mathutils.Vector(loc)
            obj.rotation_mode  = 'XYZ'
            obj.rotation_euler = (0.0, 0.0, 0.0)

    bpy.context.view_layer.update()
    print("=== T4 reset to canonical ===")

###############################################################################
# SECTION 3: Helpers
###############################################################################

def set_last_keyframe_interpolation(obj, data_path, frame, interp='LINEAR'):
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

    bpy.context.scene.frame_set(F_START)
    for h in (hinge_gy, hinge_rg, hinge_br):
        h.rotation_mode  = 'XYZ'
        h.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # ── Build parenting hierarchy — HRG is root (mirrored from T03) ────────────
    I4 = mathutils.Matrix.Identity(4)

    def attach(child, parent, local_xyz):
        child.parent                = parent
        child.matrix_parent_inverse = I4.copy()
        child.location              = mathutils.Vector(local_xyz)
        child.rotation_euler        = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

    # HRG is world root (exact T03 structure)
    # Branch 1: Green → HGY → Yellow (exact T03)
    attach(green,    hinge_rg, (-0.51,  0.51, 0.0))
    attach(hinge_gy, green,    ( 0.0,   0.0,  0.0))
    attach(yellow,   hinge_gy, ( 0.0,   0.0,  0.0))

    # Branch 2: HBR → Red → Blue (exact T03)
    attach(hinge_br, hinge_rg, ( 0.51,  0.51, 0.0))
    attach(red,      hinge_br, (-0.51, -0.51, 0.0))
    attach(blue,     red,      ( 0.51,  0.51, 0.0))

    # Parent hinge_rg (current root) under System_Rotator, preserving world transform
    system_rotator = bpy.data.objects.get(PIVOT_NAME)
    if not system_rotator:
        print(f"ERROR: {PIVOT_NAME} not found in scene")
        return False
    system_rotator.rotation_mode  = 'XYZ'
    system_rotator.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    hinge_rg_world = hinge_rg.matrix_world.copy()
    hinge_rg.parent = system_rotator
    hinge_rg.matrix_parent_inverse = system_rotator.matrix_world.inverted() @ hinge_rg_world
    bpy.context.view_layer.update()

    print("Hierarchy: System_Rotator → HRG → [Green→HGY→Yellow] + [HBR→Red→Blue]")

    # Verify hierarchy
    bpy.context.view_layer.update()
    _verify = {
        "Cube_Green":         (-0.51,  0.0,  1.0),
        "Hinge_Green_Yellow": (-0.51,  0.0,  1.0),
        "Cube_Yellow":        (-0.51,  0.0,  1.0),
        "Hinge_Blue_Red":     ( 0.51,  0.0,  1.0),
        "Cube_Red":           ( 0.0,  -0.51, 1.0),
        "Cube_Blue":          ( 0.51,  0.51, 1.0),
    }
    print("=== T4 Hierarchy World-Position Verification ===")
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

    # ── Place ball inside Green ──────────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    ball.location = BALL_GREEN_INTERIOR.copy()
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()

    # ── Use existing scene empties — NEVER create new seats ─────────────────
    seat_green = bpy.data.objects.get("Seat_Green")
    seat_blue  = bpy.data.objects.get("Seat_Blue")
    if not seat_green or not seat_blue:
        print("ERROR: Seat_Green or Seat_Blue not found in scene")
        return False

    # ── Ball constraints (source=Seat_Green, destination=Seat_Blue) ──────────
    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name   = "Latch_Green_Start"
    latch_green.target = seat_green

    latch_blue = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_blue.name   = "Latch_Blue_Side"
    latch_blue.target = seat_blue

    # ── Keyframes ────────────────────────────────────────────────────────────

    # Stage 1 (1–80): HBR +180°
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_START,    0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S1_END,   HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S2B_END,  HBR_DEG)   # hold
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_SWAP,     HBR_DEG)   # hold
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET1_END, HBR_DEG)   # hold
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET2_END, 0)

    # Stage 2a (81–120): HRG +90°
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_START,    0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S1_END,   0)          # hold Stage 1
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2A_END,  HRG_DEG)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2B_END,  HRG_DEG)    # hold
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_SWAP,     HRG_DEG)    # hold
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET1_END, 0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET2_END, 0)

    # Stage 2b (121–160): System_Rotator -90° Y
    key_rot(system_rotator, PIVOT_AXIS, PIVOT_SIGN, F_START,    0)
    key_rot(system_rotator, PIVOT_AXIS, PIVOT_SIGN, F_S2A_END,  0)           # hold through Stage 2a
    key_rot(system_rotator, PIVOT_AXIS, PIVOT_SIGN, F_S2B_END,  PIVOT_DEG)   # -90° Y by frame 160
    key_rot(system_rotator, PIVOT_AXIS, PIVOT_SIGN, F_SWAP,     PIVOT_DEG)   # hold through swap
    key_rot(system_rotator, PIVOT_AXIS, PIVOT_SIGN, F_RET1_END, 0)           # return to 0° by frame 200
    key_rot(system_rotator, PIVOT_AXIS, PIVOT_SIGN, F_RET2_END, 0)           # hold at 0°

    # Ball transfer at frame 161
    key_influence(ball, "Latch_Green_Start", F_START,    1.0)
    key_influence(ball, "Latch_Blue_Side",   F_START,    0.0)
    key_influence(ball, "Latch_Green_Start", F_S2B_END,  1.0)
    key_influence(ball, "Latch_Blue_Side",   F_S2B_END,  0.0)
    key_influence(ball, "Latch_Green_Start", F_SWAP,     0.0)
    key_influence(ball, "Latch_Blue_Side",   F_SWAP,     1.0)
    key_influence(ball, "Latch_Green_Start", F_END,      0.0)
    key_influence(ball, "Latch_Blue_Side",   F_END,      1.0)

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== T4 Complete: Green → Blue ===")
    print("Stage 1  (1–80):    HBR +180° — Blue opens")
    print("Stage 2a (81–120):  HRG +90° — Green swings")
    print("Stage 2b (121–160): Pivot −90° Y — system repositions")
    print("Frame 161: ball transfers Green → Blue")
    print("Return (162–240): all back to 0°")
    return True

###############################################################################
# SECTION 5: UI Panel
###############################################################################

class LORQB_OT_reset_t4(bpy.types.Operator):
    bl_idname      = "lorqb.reset_t4"
    bl_label       = "Reset to Base"
    bl_description = "Clear all T4 animation and parenting"
    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "T4 reset")
        return {'FINISHED'}

class LORQB_OT_run_t4(bpy.types.Operator):
    bl_idname      = "lorqb.run_t4"
    bl_label       = "Run T4: Green → Blue"
    bl_description = "Run full T4 sequence"
    def execute(self, context):
        ok = run_animation()
        self.report({'INFO'} if ok else {'ERROR'},
                    "T4 armed — play 1–240" if ok else "FAILED — see console")
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
# SECTION 6: Entry Point
###############################################################################

if __name__ == "__main__":
    for _n in ["LORQB_OT_reset_t4", "LORQB_OT_run_t4", "LORQB_PT_t4_panel"]:
        _c = getattr(bpy.types, _n, None)
        if _c:
            try:
                bpy.utils.unregister_class(_c)
            except Exception:
                pass
    for cls in _classes:
        try:
            bpy.utils.register_class(cls)
            print(f"Registered: {cls.bl_idname}")
        except Exception as e:
            print(f"ERROR: {cls.__name__}: {e}")
    print("T4 panel registered. Use 'Run T4' button to arm animation.")
