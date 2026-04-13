# ============================================================================
# T04_hinge_test.py  (Blender 5.0.1)
#
# Hinge isolation test — correct branching hierarchy.
# No ball. No constraints. No physics. No bones. No drivers.
#
# Physical chain: Yellow — [HGY] — Green — [HRG] — Red — [HBR] — Blue
#
# Blender hierarchy (mirrors T03 structure, Green replaces HRG as root):
#
#   Cube_Green  (world root — never animated)
#   ├── Hinge_Green_Yellow  (HGY)  → Cube_Yellow   [passive side]
#   └── Hinge_Red_Green     (HRG)  → Cube_Red
#                                       └── Hinge_Blue_Red (HBR) → Cube_Blue
#
# Why this is correct:
#   HGY connects Green ↔ Yellow — must branch from Green, not from Blue.
#   HRG connects Green ↔ Red    — branches from Green on the active side.
#   HBR connects Red  ↔ Blue    — branches from Red.
#
#   When HRG rotates: Green, HGY, Yellow stay fixed (Green is parent).
#                     Red, HBR, Blue swing. No gap at any hinge.
#   When HBR rotates: Red, HRG, Green, HGY, Yellow stay fixed.
#                     Blue swings. No gap at HRG or HGY.
#
# PASS criteria:
#   1. HGY local rotation = (0,0,0) at every frame.
#   2. Green world position constant throughout.
#   3. HGY world position constant (it is fixed under Green).
#   4. Red world position = HRG world position (Red local = 0,0,0 from HRG).
#   5. At frame 160: Blue world position = Green world position (transfer ready).
# ============================================================================

import bpy
import math
import mathutils

# ─── Constants ───────────────────────────────────────────────────────────────

F_START    = 1
F_S1_END   = 80
F_S2A_END  = 120
F_S2_END   = 160
F_RET1_END = 200
F_RET2_END = 240
F_END      = 240

HBR_AXIS  = 0        # X
HBR_SIGN  = +1.0     # TODO: verify empirically
HBR_DEG   = 180.0

HRG_AXIS    = 1      # Y
HRG_SIGN    = -1.0   # TODO: verify empirically
HRG_DEG_2A  = 90.0
HRG_DEG_2B  = 180.0

POSITION_TOL = 0.005
SAMPLE_STEP  = 10


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _set_interp(obj, dp, frame, interp='LINEAR'):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action  = obj.animation_data.action
    fcurves = None
    try:
        if action.fcurves:
            fcurves = action.fcurves
    except AttributeError:
        pass
    if fcurves is None:
        try:
            bag = action.layers[0].strips[0].channelbag_for_slot(action.slots[0])
            if bag:
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
        if dp in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp


def key_rot(obj, axis, sign, frame, degrees):
    bpy.context.scene.frame_set(frame)
    obj.rotation_mode        = 'XYZ'
    obj.rotation_euler[axis] = sign * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=axis, frame=frame)
    _set_interp(obj, "rotation_euler", frame, 'LINEAR')


# ─── Reset ───────────────────────────────────────────────────────────────────

def reset():
    names = ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
             "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]
    for n in names:
        obj = bpy.data.objects.get(n)
        if obj and obj.animation_data:
            obj.animation_data_clear()
    for n in ["Cube_Yellow", "Hinge_Green_Yellow", "Cube_Blue", "Hinge_Blue_Red",
              "Cube_Red", "Hinge_Red_Green", "Cube_Green"]:
        obj = bpy.data.objects.get(n)
        if obj and obj.parent:
            obj.parent = None
    bpy.context.view_layer.update()
    canonical = {
        "Cube_Green":         (-0.51,  0.0,  1.0),
        "Hinge_Green_Yellow": (-0.51,  0.0,  1.0),
        "Cube_Yellow":        (-0.51,  0.0,  1.0),
        "Hinge_Red_Green":    ( 0.0,  -0.51, 1.0),
        "Cube_Red":           ( 0.0,  -0.51, 1.0),
        "Hinge_Blue_Red":     ( 0.51,  0.0,  1.0),
        "Cube_Blue":          ( 0.51,  0.0,  1.0),
    }
    for n, loc in canonical.items():
        obj = bpy.data.objects.get(n)
        if obj:
            obj.location       = mathutils.Vector(loc)
            obj.rotation_mode  = 'XYZ'
            obj.rotation_euler = (0.0, 0.0, 0.0)
            obj.scale          = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    print("=== reset complete ===")


# ─── Test ────────────────────────────────────────────────────────────────────

def run_hinge_test():
    print()
    print("=" * 70)
    print("  T04 HINGE TEST  —  correct branching hierarchy")
    print("  Physical chain: Yellow-[HGY]-Green-[HRG]-Red-[HBR]-Blue")
    print("=" * 70)

    reset()

    blue     = bpy.data.objects.get("Cube_Blue")
    red      = bpy.data.objects.get("Cube_Red")
    green    = bpy.data.objects.get("Cube_Green")
    yellow   = bpy.data.objects.get("Cube_Yellow")
    hinge_br = bpy.data.objects.get("Hinge_Blue_Red")
    hinge_rg = bpy.data.objects.get("Hinge_Red_Green")
    hinge_gy = bpy.data.objects.get("Hinge_Green_Yellow")

    missing = [n for n, o in [
        ("Cube_Blue", blue), ("Cube_Red", red), ("Cube_Green", green),
        ("Cube_Yellow", yellow), ("Hinge_Blue_Red", hinge_br),
        ("Hinge_Red_Green", hinge_rg), ("Hinge_Green_Yellow", hinge_gy),
    ] if o is None]
    if missing:
        print("ERROR: Missing:", missing)
        return

    # ── HINGE SKILL ──────────────────────────────────────────────────────────
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()
    wp  = lambda o: o.matrix_world.translation.copy()
    pre = {k: wp(o) for k, o in [
        ("green", green), ("hgy", hinge_gy), ("yellow", yellow),
        ("hrg",   hinge_rg), ("red", red),
        ("hbr",   hinge_br), ("blue", blue),
    ]}
    print("\n[SKILL] Canonical world positions:")
    for k, v in pre.items():
        print(f"  {k:8s}: {tuple(round(x, 4) for x in v)}")

    I4 = mathutils.Matrix.Identity(4)

    def attach(child, parent_obj, world_target):
        local = world_target - parent_obj.matrix_world.translation
        child.parent                = parent_obj
        child.matrix_parent_inverse = I4.copy()
        child.location              = mathutils.Vector(local)
        child.rotation_euler        = (0.0, 0.0, 0.0)
        child.scale                 = (1.0, 1.0, 1.0)
        bpy.context.view_layer.update()
        actual = child.matrix_world.translation
        diff   = (actual - world_target).length
        tag    = "OK  " if diff < POSITION_TOL else f"FAIL(err={diff:.5f})"
        print(f"  {tag} {child.name:24s}  world={tuple(round(x, 4) for x in actual)}")

    # ── Build hierarchy ───────────────────────────────────────────────────────
    #
    #   Green (root)
    #   ├── HGY → Yellow          (passive: Green-Yellow hinge stays at Green)
    #   └── HRG → Red → HBR → Blue  (active chain)
    #
    print("\n[SKILL] Building hierarchy:")
    attach(hinge_gy, green,    pre["hgy"])    # HGY  → Green  (passive side)
    attach(yellow,   hinge_gy, pre["yellow"]) # Yellow → HGY
    attach(hinge_rg, green,    pre["hrg"])    # HRG  → Green  (active side)
    attach(red,      hinge_rg, pre["red"])    # Red  → HRG
    attach(hinge_br, red,      pre["hbr"])    # HBR  → Red
    attach(blue,     hinge_br, pre["blue"])   # Blue → HBR

    bpy.context.scene.frame_set(F_START)
    for h in (hinge_br, hinge_rg, hinge_gy):
        h.rotation_mode  = 'XYZ'
        h.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # ── Validate ─────────────────────────────────────────────────────────────
    expected = {
        "Hinge_Green_Yellow": "Cube_Green",
        "Cube_Yellow":        "Hinge_Green_Yellow",
        "Hinge_Red_Green":    "Cube_Green",
        "Cube_Red":           "Hinge_Red_Green",
        "Hinge_Blue_Red":     "Cube_Red",
        "Cube_Blue":          "Hinge_Blue_Red",
    }
    ok = True
    print("\n[VALIDATE] Hierarchy:")
    for name, exp in expected.items():
        obj    = bpy.data.objects.get(name)
        actual = obj.parent.name if (obj and obj.parent) else "None"
        tag    = "OK  " if actual == exp else "FAIL"
        if tag == "FAIL":
            ok = False
        print(f"  {tag} {name}: parent={actual}  (expected={exp})")
    if not ok:
        print("ERROR: Hierarchy FAILED — aborting.")
        return

    # ── Keyframes ─────────────────────────────────────────────────────────────
    print("\n[KEYFRAMES]")
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_START,    0)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S1_END,   HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_S2_END,   HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET1_END, HBR_DEG)
    key_rot(hinge_br, HBR_AXIS, HBR_SIGN, F_RET2_END, 0)
    print(f"  HBR: 0→{HBR_DEG}° (1–{F_S1_END}), hold, →0° (–{F_RET2_END})")

    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_START,    0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S1_END,   0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2A_END,  HRG_DEG_2A)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_S2_END,   HRG_DEG_2B)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET1_END, 0)
    key_rot(hinge_rg, HRG_AXIS, HRG_SIGN, F_RET2_END, 0)
    print(f"  HRG: hold (1–{F_S1_END}), 0→{HRG_DEG_2A}° (–{F_S2A_END}), "
          f"→{HRG_DEG_2B}° (–{F_S2_END}), →0° (–{F_RET1_END})")
    print("  HGY: NO keyframes.")

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END

    # ── Diagnostics ───────────────────────────────────────────────────────────
    green_w0  = pre["green"]
    hgy_w0    = pre["hgy"]
    hrg_w0    = pre["hrg"]
    red_w0    = pre["red"]

    print()
    print("FRAME-BY-FRAME DIAGNOSTIC:")
    hdr = (f"{'Fr':>4}  {'HBR.x°':>7}  {'HRG.y°':>7}  "
           f"{'HGY.x°':>8}  {'HGY.y°':>8}  {'HGY.z°':>8}  "
           f"{'Blue world':>20}  STATUS")
    print(hdr)
    print("-" * len(hdr))

    fails = []

    for f in range(F_START, F_END + 1, SAMPLE_STEP):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()

        hbr_d  = math.degrees(hinge_br.rotation_euler[HBR_AXIS])
        hrg_d  = math.degrees(hinge_rg.rotation_euler[HRG_AXIS])
        hgy_rx = math.degrees(hinge_gy.rotation_euler[0])
        hgy_ry = math.degrees(hinge_gy.rotation_euler[1])
        hgy_rz = math.degrees(hinge_gy.rotation_euler[2])

        green_w = green.matrix_world.translation.copy()
        hgy_w   = hinge_gy.matrix_world.translation.copy()
        hrg_w   = hinge_rg.matrix_world.translation.copy()
        red_w   = red.matrix_world.translation.copy()
        blue_w  = blue.matrix_world.translation.copy()

        issues = []

        # 1: HGY local rotation must be zero
        if abs(hgy_rx) > 0.01 or abs(hgy_ry) > 0.01 or abs(hgy_rz) > 0.01:
            s = f"HGY-ROTATING({hgy_rx:.3f},{hgy_ry:.3f},{hgy_rz:.3f})"
            issues.append(s); fails.append(f"f{f}: {s}")

        # 2: Green must not move (world root)
        if (green_w - green_w0).length > POSITION_TOL:
            s = f"GREEN-MOVED(d={(green_w-green_w0).length:.4f})"
            issues.append(s); fails.append(f"f{f}: {s}")

        # 3: HGY must not move (child of fixed Green, local 0,0,0)
        if (hgy_w - hgy_w0).length > POSITION_TOL:
            s = f"HGY-MOVED(d={(hgy_w-hgy_w0).length:.4f})"
            issues.append(s); fails.append(f"f{f}: {s}")

        # 4: HRG must not translate (it only rotates; child of fixed Green)
        if (hrg_w - hrg_w0).length > POSITION_TOL:
            s = f"HRG-TRANSLATED(d={(hrg_w-hrg_w0).length:.4f})"
            issues.append(s); fails.append(f"f{f}: {s}")

        # 5: Red must stay at HRG's world position (Red local = 0,0,0 from HRG)
        if (red_w - hrg_w).length > POSITION_TOL:
            s = f"RED-DRIFTED(d={(red_w-hrg_w).length:.4f})"
            issues.append(s); fails.append(f"f{f}: {s}")

        bw = str(tuple(round(x, 3) for x in blue_w))
        st = " | ".join(issues) if issues else "OK"
        print(f"  {f:3d}  {hbr_d:7.2f}  {hrg_d:7.2f}  "
              f"{hgy_rx:8.4f}  {hgy_ry:8.4f}  {hgy_rz:8.4f}  "
              f"{bw:>20}  {st}")

    print("-" * len(hdr))

    # Geometry check: Blue at Green's position at frame 160
    bpy.context.scene.frame_set(F_S2_END)
    bpy.context.view_layer.update()
    blue_f160 = blue.matrix_world.translation.copy()
    dist      = (blue_f160 - green_w0).length
    align_ok  = dist < 0.05
    print(f"\n[GEOMETRY] Frame {F_S2_END}: Blue={tuple(round(x,4) for x in blue_f160)}"
          f"  Green={tuple(round(x,4) for x in green_w0)}"
          f"  dist={dist:.4f}  {'ALIGNED — transfer ready' if align_ok else 'NOT ALIGNED'}")
    if not align_ok:
        fails.append(f"Frame {F_S2_END}: Blue not at Green position (dist={dist:.4f})")

    # Summary
    print()
    if fails:
        print(f"FAIL — {len(fails)} issue(s):")
        for e in fails:
            print(f"  ✗ {e}")
    else:
        print("PASS:")
        print("  ✓ HGY local rotation = (0,0,0) throughout.")
        print("  ✓ Green world position constant (correct root).")
        print("  ✓ HGY world position constant (Green-Yellow hinge stays at Green).")
        print("  ✓ HRG world position constant (no translation, only rotation).")
        print("  ✓ Red world position = HRG world position (zero drift).")
        print(f"  ✓ Blue arrived at Green's world position at frame {F_S2_END}.")
        print("  ✓ No detachment at any hinge.")
    print("=" * 70)
    bpy.context.scene.frame_set(F_START)


# ─── UI ──────────────────────────────────────────────────────────────────────

class LORQB_OT_t4_hinge_test(bpy.types.Operator):
    bl_idname      = "lorqb.t4_hinge_test"
    bl_label       = "Run T4 Hinge Test"
    bl_description = "Proves correct branching hierarchy: no detachment at any hinge"

    def execute(self, context):
        run_hinge_test()
        self.report({'INFO'}, "T4 hinge test — see console")
        return {'FINISHED'}


class LORQB_PT_t4_test_panel(bpy.types.Panel):
    bl_label       = "LorQB — T4 Hinge Test"
    bl_idname      = "LORQB_PT_t4_test_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        self.layout.operator("lorqb.t4_hinge_test", text="Run T4 Hinge Test", icon='PLAY')
        self.layout.label(text="Check System Console for PASS/FAIL", icon='INFO')


for _n in ["LORQB_OT_t4_hinge_test", "LORQB_PT_t4_test_panel"]:
    _c = getattr(bpy.types, _n, None)
    if _c:
        try:
            bpy.utils.unregister_class(_c)
        except Exception:
            pass

bpy.utils.register_class(LORQB_OT_t4_hinge_test)
bpy.utils.register_class(LORQB_PT_t4_test_panel)

if __name__ == "__main__":
    run_hinge_test()
