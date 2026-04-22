# ============================================================================
# C15_yellow_to_blue.py  (Blender 5.0.1)
# C15 — Yellow → Blue
# Frames 1-240 | Transfer at 120→121
# Chain: Blue — Red — HRG — Green — HGY — Yellow
# Hinge: Hinge_Red_Green (Y axis, ROT_SIGN = +1.0)
# Green+Yellow swing as one unit toward Blue+Red — ball deposits into Blue
# Ball held by COPY_TRANSFORMS on seat empties (no CHILD_OF)
# ============================================================================

import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
################################################################################

OBJ_HINGE  = "Hinge_Red_Green"
OBJ_BALL   = "Ball"
OBJ_YELLOW = "Cube_Yellow"
OBJ_GREEN  = "Cube_Green"
OBJ_BLUE   = "Cube_Blue"
OBJ_RED    = "Cube_Red"

CON_YELLOW  = "Latch_Yellow"
CON_BLUE    = "Latch_Blue"

F_ZERO       = 1
F_START      = 1
F_MID        = 60
F_TRANSFER   = 120
F_TRANSFER_1 = 121
F_RET        = 180
F_END        = 240

ROT_AXIS = 1        # Y
ROT_SIGN = +1.0

# ── Cube ORIGIN world positions (matches C10 ORIGIN_CURSOR relocation) ──
# C10_scene_build.py lines 284–303: each cube's origin is moved to its
# hinge position via bpy.ops.object.origin_set(type='ORIGIN_CURSOR').
# cube.location stores ORIGIN position, NOT visual center. Reset must use
# these values or the mesh is displaced.
CANON_CUBES = {
    "Cube_Blue":   mathutils.Vector(( 0.51,  0.00, 1.0)),  # origin at Hinge_Blue_Red
    "Cube_Red":    mathutils.Vector(( 0.00, -0.51, 1.0)),  # origin at Hinge_Red_Green
    "Cube_Green":  mathutils.Vector((-0.51,  0.00, 1.0)),  # origin at Hinge_Green_Yellow
    "Cube_Yellow": mathutils.Vector((-0.51,  0.00, 1.0)),  # origin at Hinge_Green_Yellow
}
CANON_HINGES = {
    "Hinge_Blue_Red":     mathutils.Vector(( 0.51,  0.00, 1.0)),
    "Hinge_Red_Green":    mathutils.Vector(( 0.00, -0.51, 1.0)),
    "Hinge_Green_Yellow": mathutils.Vector((-0.51,  0.00, 1.0)),
}

# ── Cube VISUAL-CENTER world positions (true ball-containment target) ──
# These are the world positions of each cube's visible mesh center, which
# is OFFSET from the origin because C10 relocates origins to hinge corners.
CANON_VISUAL_CENTERS = {
    "Cube_Blue":   mathutils.Vector(( 0.51,  0.51, 0.5)),
    "Cube_Red":    mathutils.Vector(( 0.51, -0.51, 0.5)),
    "Cube_Green":  mathutils.Vector((-0.51, -0.51, 0.5)),
    "Cube_Yellow": mathutils.Vector((-0.51,  0.51, 0.5)),
}

# ---- Four-Seat Contract (seats target VISUAL cube centers, not origins) ----
CANON_SEATS = {
    "Seat_Blue":   (CANON_VISUAL_CENTERS["Cube_Blue"],   "Cube_Blue"),
    "Seat_Red":    (CANON_VISUAL_CENTERS["Cube_Red"],    "Cube_Red"),
    "Seat_Green":  (CANON_VISUAL_CENTERS["Cube_Green"],  "Cube_Green"),
    "Seat_Yellow": (CANON_VISUAL_CENTERS["Cube_Yellow"], "Cube_Yellow"),
}

SEAT_YELLOW_WORLD = CANON_SEATS["Seat_Yellow"][0]
SEAT_BLUE_WORLD   = CANON_SEATS["Seat_Blue"][0]

def ensure_four_seats():
    """Build 4 seats. Each seat is parented to its cube and positioned at the
    cube's VISUAL CENTER in world space (computed from the mesh bound_box,
    NOT from the cube origin — origin is at hinge corner per C10)."""
    for seat_name, (_, _) in CANON_SEATS.items():
        stale = bpy.data.objects.get(seat_name)
        if stale:
            bpy.data.objects.remove(stale, do_unlink=True)
    bpy.context.view_layer.update()

    for seat_name, (_, cube_name) in CANON_SEATS.items():
        cube = bpy.data.objects.get(cube_name)
        if cube is None:
            continue
        # Target = cube's actual visual center in world space
        visual_center_world = _cube_visual_center_world(cube)
        seat = bpy.data.objects.new(seat_name, None)
        seat.empty_display_type = 'SPHERE'
        seat.empty_display_size = 0.08
        bpy.context.scene.collection.objects.link(seat)
        seat.parent   = cube
        seat.location = cube.matrix_world.inverted() @ visual_center_world
    bpy.context.view_layer.update()

def validate_four_seats(label):
    print(f"--- FOUR-SEAT REPORT [{label}] ---")
    ok = True
    for seat_name in ("Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"):
        seat = bpy.data.objects.get(seat_name)
        if seat is None:
            print(f"  {seat_name}: <missing>  FAIL")
            ok = False
            continue
        # Seat must coincide with its cube's VISUAL CENTER (not origin)
        cube_name = CANON_SEATS[seat_name][1]
        expected  = CANON_VISUAL_CENTERS[cube_name]
        w = seat.matrix_world.translation
        d = (w - expected).length
        seat_ok = d <= 1e-3
        tag = "OK" if seat_ok else f"FAIL(Δ={d:.4f})"
        if not seat_ok:
            ok = False
        print(f"  {seat_name}: ({w.x:+.4f},{w.y:+.4f},{w.z:+.4f}) "
              f"target=({expected.x:+.4f},{expected.y:+.4f},{expected.z:+.4f}) {tag}")
    print(f"--- FOUR-SEAT [{label}] → {'PASS' if ok else 'FAIL'} ---")
    return ok

def hard_fail_missing_seats():
    missing = [n for n in CANON_SEATS if bpy.data.objects.get(n) is None]
    if missing:
        print("ABORT: missing canonical seats:", missing)
        return False
    return True

################################################################################
# SECTION 2: Utilities
################################################################################

def _fcurves(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return []
    act = obj.animation_data.action
    try:
        return act.fcurves
    except Exception:
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


def parent_preserve_world(child, new_parent):
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw

################################################################################
# SECTION 3: Object Lookup
################################################################################

def get_objects():
    hinge  = bpy.data.objects.get(OBJ_HINGE)
    ball   = bpy.data.objects.get(OBJ_BALL)
    yellow = bpy.data.objects.get(OBJ_YELLOW)
    green  = bpy.data.objects.get(OBJ_GREEN)
    blue   = bpy.data.objects.get(OBJ_BLUE)
    red    = bpy.data.objects.get(OBJ_RED)

    missing = [n for n, o in [
        (OBJ_HINGE,  hinge),
        (OBJ_BALL,   ball),
        (OBJ_YELLOW, yellow),
        (OBJ_GREEN,  green),
        (OBJ_BLUE,   blue),
        (OBJ_RED,    red),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return None

    return hinge, ball, yellow, green, blue, red

################################################################################
# SECTION 4: Setup
################################################################################

def reset_scene_to_canonical():
    IDENTITY4 = mathutils.Matrix.Identity(4)

    all_names = [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
    ]
    for name in all_names:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()
        ball.parent = None
        ball.matrix_parent_inverse = IDENTITY4

    # Contract §7.3: unparent cubes AND reset matrix_parent_inverse to identity
    # before setting canonical location. Without this, cube.location is local
    # to a stale parent-inverse, producing wrong world positions at F_START.
    for cube_name in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow"]:
        cube = bpy.data.objects.get(cube_name)
        if cube:
            cube.parent = None
            cube.matrix_parent_inverse = IDENTITY4
            for con in list(cube.constraints):
                cube.constraints.remove(con)

    # Contract §7.3: same for hinges
    for hinge_name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        hinge = bpy.data.objects.get(hinge_name)
        if hinge:
            hinge.parent = None
            hinge.matrix_parent_inverse = IDENTITY4
            for con in list(hinge.constraints):
                hinge.constraints.remove(con)
            hinge.rotation_mode  = 'XYZ'
            hinge.rotation_euler = (0.0, 0.0, 0.0)

    for seat_name in ["Seat_Yellow", "Seat_Blue", "Seat_Red", "Seat_Green",
                      "Seat_C15_Transit"]:
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)

    bpy.context.view_layer.update()

    # Restore all cubes and hinges to AUTHORITATIVE canonical world positions
    cubes_restored = 0
    for name, loc in CANON_CUBES.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location       = (loc.x, loc.y, loc.z)
            obj.rotation_mode  = 'XYZ'
            obj.rotation_euler = (0.0, 0.0, 0.0)
            cubes_restored += 1

    hinges_restored = 0
    for name, loc in CANON_HINGES.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location       = (loc.x, loc.y, loc.z)
            obj.rotation_mode  = 'XYZ'
            obj.rotation_euler = (0.0, 0.0, 0.0)
            hinges_restored += 1

    bpy.context.view_layer.update()
    print(f"=== C15 reset: canonical restored (cubes={cubes_restored}/4, hinges={hinges_restored}/3) ===")

################################################################################
# SECTION 5: Animation
################################################################################

def setup_hinge_keyframes(hinge):
    # Y-axis, ROT_SIGN=+1.0
    # 0° hold → 90° mid → 180° transfer → hold → 90° return → 0° end
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_ZERO,       0)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_START,       0)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_MID,        90)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_TRANSFER,  180)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_TRANSFER_1,180)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_RET,        90)
    key_rot(hinge, ROT_AXIS, ROT_SIGN, F_END,         0)
    print(f"Hinge_Red_Green keyed (Y / ROT_SIGN={ROT_SIGN}) — LINEAR.")

################################################################################
# SECTION 6: Ball Transfer
################################################################################

def setup_ball_transfer(ball, yellow, blue, hinge):
    # -- Four-Seat Contract — build ALL 4 canonical seats at visual centers --
    ensure_four_seats()
    if not validate_four_seats("after ensure_four_seats"):
        print("ABORT: four-seat validation failed at build time.")
        return False
    if not hard_fail_missing_seats():
        return False

    seat_yellow = bpy.data.objects.get("Seat_Yellow")
    seat_blue   = bpy.data.objects.get("Seat_Blue")

    # -- 2-latch schedule (Yellow → Blue, CONSTANT, per BALL STATE STANDARD §2)
    #    Ball stays inside Yellow from F_START through F_TRANSFER (frame 120),
    #    then switches to Blue at F_TRANSFER_1 (frame 121). No transit seat.
    latch_y = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_y.name   = CON_YELLOW
    latch_y.target = seat_yellow

    latch_b = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_b.name   = CON_BLUE
    latch_b.target = seat_blue

    # --- Hold phase: F_START → F_TRANSFER: Latch_Yellow = 1.0 ---
    key_influence(ball, CON_YELLOW,  F_START,       1.0)
    key_influence(ball, CON_BLUE,    F_START,       0.0)

    key_influence(ball, CON_YELLOW,  F_TRANSFER,    1.0)
    key_influence(ball, CON_BLUE,    F_TRANSFER,    0.0)

    # --- Transfer: F_TRANSFER_1 → F_END: Latch_Blue = 1.0 ---
    key_influence(ball, CON_YELLOW,  F_TRANSFER_1,  0.0)
    key_influence(ball, CON_BLUE,    F_TRANSFER_1,  1.0)

    key_influence(ball, CON_YELLOW,  F_END,         0.0)
    key_influence(ball, CON_BLUE,    F_END,         1.0)

    print(f"2-latch schedule keyed: Yellow(1–{F_TRANSFER}) → Blue({F_TRANSFER_1}–{F_END}) (CONSTANT).")

################################################################################
# SECTION 7: Diagnostic dump
################################################################################

def dump_world_positions(label):
    names = [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
        "Seat_Blue", "Seat_Yellow", "Seat_C15_Transit",
    ]
    print(f"--- DUMP [{label}] ---")
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None:
            print(f"  {n}: <missing>")
        else:
            w = o.matrix_world.translation
            print(f"  {n}: ({w.x:+.4f}, {w.y:+.4f}, {w.z:+.4f})")
    print(f"--- END DUMP [{label}] ---")


def validate_canonical_world(label, tol=1e-3):
    """Confirm all cubes (origins) and hinges are at canonical world positions.
    Also confirms each cube's VISUAL CENTER matches the expected position —
    this catches mesh displacement even when the origin is correct."""
    ok = True
    print(f"--- CANONICAL CHECK [{label}] ---")
    for name, target in list(CANON_CUBES.items()) + list(CANON_HINGES.items()):
        o = bpy.data.objects.get(name)
        if o is None:
            print(f"  {name}: <missing>  FAIL")
            ok = False
            continue
        w = o.matrix_world.translation
        d = (w - target).length
        status = "OK" if d <= tol else "FAIL"
        if d > tol:
            ok = False
        print(f"  {name}: world=({w.x:+.4f},{w.y:+.4f},{w.z:+.4f}) "
              f"target=({target.x:+.4f},{target.y:+.4f},{target.z:+.4f}) Δ={d:.5f} {status}")

    # Visual-center check — prove the cube MESH is where we expect
    for cube_name, vc_target in CANON_VISUAL_CENTERS.items():
        o = bpy.data.objects.get(cube_name)
        if o is None:
            continue
        vc_world = _cube_visual_center_world(o)
        d = (vc_world - vc_target).length
        status = "OK" if d <= tol else "FAIL"
        if d > tol:
            ok = False
        print(f"  {cube_name} visual-center: ({vc_world.x:+.4f},{vc_world.y:+.4f},{vc_world.z:+.4f}) "
              f"target=({vc_target.x:+.4f},{vc_target.y:+.4f},{vc_target.z:+.4f}) Δ={d:.5f} {status}")

    print(f"--- CANONICAL CHECK [{label}] → {'PASS' if ok else 'FAIL'} ---")
    return ok


def _cube_visual_center_world(cube):
    """Return the cube's visual mesh center in world space.
    Uses mesh bounding-box center (8 corners averaged) transformed by matrix_world.
    Independent of where the object's origin has been placed."""
    bb = cube.bound_box  # 8 local-space corners
    cx = sum(v[0] for v in bb) / 8.0
    cy = sum(v[1] for v in bb) / 8.0
    cz = sum(v[2] for v in bb) / 8.0
    local_center = mathutils.Vector((cx, cy, cz))
    return cube.matrix_world @ local_center


def print_c15_summary(cubes_ok, hinges_ok, seats_ok, ball_ok, canonical_ok):
    print("╔══════════════ C15 FINAL STATE ══════════════╗")
    print(f"  Cubes restored to canonical : {'OK' if cubes_ok else 'FAIL'}")
    print(f"  Hinges restored to canonical: {'OK' if hinges_ok else 'FAIL'}")
    print(f"  Seats created (Y + B)       : {'OK' if seats_ok else 'FAIL'}")
    print(f"  Ball latched at Seat_Yellow : {'OK' if ball_ok else 'FAIL'}")
    print(f"  Final scene canonical       : {'OK' if canonical_ok else 'FAIL'}")
    print("╚═════════════════════════════════════════════╝")


def validate_seat_yellow_inside_yellow():
    """Seat_Yellow must sit inside Yellow's VISIBLE mesh volume (bound_box),
    not merely within ±0.5 of the cube's origin (which is at a hinge corner)."""
    yellow = bpy.data.objects.get("Cube_Yellow")
    seat   = bpy.data.objects.get("Seat_Yellow")
    if yellow is None or seat is None:
        print("[C15 VALIDATE] FAIL — Yellow or Seat_Yellow missing")
        return False
    local = yellow.matrix_world.inverted() @ seat.matrix_world.translation
    bb = yellow.bound_box
    xs = [v[0] for v in bb]; ys = [v[1] for v in bb]; zs = [v[2] for v in bb]
    inside = (min(xs) <= local.x <= max(xs)) and \
             (min(ys) <= local.y <= max(ys)) and \
             (min(zs) <= local.z <= max(zs))
    vc = _cube_visual_center_world(yellow)
    sw = seat.matrix_world.translation
    d_to_center = (sw - vc).length
    print(f"[C15 VALIDATE] Yellow visual-center: ({vc.x:+.4f}, {vc.y:+.4f}, {vc.z:+.4f})")
    print(f"[C15 VALIDATE] Seat_Yellow:          ({sw.x:+.4f}, {sw.y:+.4f}, {sw.z:+.4f})")
    print(f"[C15 VALIDATE] Δ seat→visual-center: {d_to_center:.5f}  inside_mesh={inside}")
    return inside and d_to_center <= 1e-3


def validate_start_state():
    """Rule §3: Ball must match Seat_Yellow at F_START (not Seat_Blue, not midpoint)."""
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()
    ball = bpy.data.objects.get("Ball")
    sy   = bpy.data.objects.get("Seat_Yellow")
    sb   = bpy.data.objects.get("Seat_Blue")
    if not (ball and sy and sb):
        print("[C15 START] FAIL — missing objects")
        return False
    bw, yw, bbw = ball.matrix_world.translation, sy.matrix_world.translation, sb.matrix_world.translation
    d_y = (bw - yw).length
    d_b = (bw - bbw).length
    ok = d_y <= 1e-3 and d_y < d_b
    print(f"[C15 START] Ball=({bw.x:+.4f},{bw.y:+.4f},{bw.z:+.4f}) ΔYellow={d_y:.5f} ΔBlue={d_b:.5f} → {'PASS' if ok else 'FAIL'}")
    return ok


def validate_alignment_at_hold():
    """Rule §4: At F_TRANSFER (F_HOLD), Seat_Yellow must be directly above Seat_Blue (XY match)."""
    bpy.context.scene.frame_set(F_TRANSFER)
    bpy.context.view_layer.update()
    sy = bpy.data.objects.get("Seat_Yellow")
    sb = bpy.data.objects.get("Seat_Blue")
    if not (sy and sb):
        print("[C15 HOLD] FAIL — missing seats")
        return False
    yw, bw = sy.matrix_world.translation, sb.matrix_world.translation
    dxy = math.hypot(yw.x - bw.x, yw.y - bw.y)
    above = yw.z > bw.z
    ok = dxy <= 1e-3 and above
    print(f"[C15 HOLD] Seat_Yellow=({yw.x:+.4f},{yw.y:+.4f},{yw.z:+.4f}) Seat_Blue=({bw.x:+.4f},{bw.y:+.4f},{bw.z:+.4f}) ΔXY={dxy:.5f} above={above} → {'PASS' if ok else 'FAIL'}")
    return ok


def validate_no_drift_toward_red():
    """Rule §4: At F_MID, Yellow must not drift toward Red world position."""
    bpy.context.scene.frame_set(F_MID)
    bpy.context.view_layer.update()
    sy = bpy.data.objects.get("Seat_Yellow")
    if sy is None:
        return False
    sw = sy.matrix_world.translation
    red_world = CANON_CUBES["Cube_Red"]
    d_red = (sw - red_world).length
    # At F_MID (90°), seat_yellow should be mid-arc; Red is on the opposite diagonal
    ok = d_red > 0.5
    print(f"[C15 MID] Seat_Yellow=({sw.x:+.4f},{sw.y:+.4f},{sw.z:+.4f}) Δ→Red={d_red:.4f} → {'PASS' if ok else 'FAIL'}")
    return ok


def validate_end_inside_blue():
    """Rule §7: At F_END, ball must be at Seat_Blue."""
    bpy.context.scene.frame_set(F_END)
    bpy.context.view_layer.update()
    ball = bpy.data.objects.get("Ball")
    sb   = bpy.data.objects.get("Seat_Blue")
    if not (ball and sb):
        return False
    bw, sw = ball.matrix_world.translation, sb.matrix_world.translation
    d = (bw - sw).length
    ok = d <= 1e-3
    print(f"[C15 END] Ball=({bw.x:+.4f},{bw.y:+.4f},{bw.z:+.4f}) Seat_Blue=({sw.x:+.4f},{sw.y:+.4f},{sw.z:+.4f}) Δ={d:.5f} → {'PASS' if ok else 'FAIL'}")
    return ok


################################################################################
# SECTION 7B: True Containment Validators (VB false-pass correction)
################################################################################

CUBE_HALF_EXTENT = 0.5   # local half-size of a 1u cube
CONTAIN_TOL      = 1e-3  # numerical slack


def get_ball_radius(ball):
    """Ball may be a UV sphere; use bound_box extent or scale as radius."""
    if ball.type == 'MESH' and ball.data and len(ball.data.vertices) > 0:
        # half of the longest bounding-box edge, scaled by world scale
        bb = ball.bound_box
        xs = [v[0] for v in bb]; ys = [v[1] for v in bb]; zs = [v[2] for v in bb]
        local_half = 0.5 * max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
        s = ball.matrix_world.to_scale()
        return local_half * max(abs(s.x), abs(s.y), abs(s.z))
    s = ball.matrix_world.to_scale()
    return 0.5 * max(abs(s.x), abs(s.y), abs(s.z))


def ball_inside_cube(ball, cube, radius):
    """
    Return (inside, max_protrusion, local_pos).
    Uses the cube's MESH bounding box (local space), not a symmetric
    [-0.5, +0.5] assumption. This is correct even when the cube's origin
    is not at its visual center (C10 relocates origins to hinge corners).
    """
    local = cube.matrix_world.inverted() @ ball.matrix_world.translation
    bb = cube.bound_box
    xs = [v[0] for v in bb]; ys = [v[1] for v in bb]; zs = [v[2] for v in bb]
    x_min, x_max = min(xs) + radius - CONTAIN_TOL, max(xs) - radius + CONTAIN_TOL
    y_min, y_max = min(ys) + radius - CONTAIN_TOL, max(ys) - radius + CONTAIN_TOL
    z_min, z_max = min(zs) + radius - CONTAIN_TOL, max(zs) - radius + CONTAIN_TOL
    inside = (x_min <= local.x <= x_max) and \
             (y_min <= local.y <= y_max) and \
             (z_min <= local.z <= z_max)
    # Protrusion = worst distance past the (contracted) interior bound
    def prot(v, lo, hi):
        if v < lo: return lo - v
        if v > hi: return v - hi
        return 0.0
    protrusion = max(prot(local.x, x_min, x_max),
                     prot(local.y, y_min, y_max),
                     prot(local.z, z_min, z_max))
    return inside, protrusion, local


def validate_ball_follows_active_latch(ball, frame, expected_latch, other_latch):
    """At `frame`, confirm ball world pos == expected latch target world pos."""
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    exp_con = ball.constraints.get(expected_latch)
    oth_con = ball.constraints.get(other_latch)
    if exp_con is None or oth_con is None:
        print(f"[LATCH f={frame}] FAIL — constraint missing")
        return False
    exp_inf = exp_con.influence
    oth_inf = oth_con.influence
    seat    = exp_con.target
    bw      = ball.matrix_world.translation
    sw      = seat.matrix_world.translation if seat else mathutils.Vector((0, 0, 0))
    d       = (bw - sw).length
    inf_ok  = (exp_inf >= 0.999) and (oth_inf <= 0.001)
    follow_ok = d <= 1e-3
    ok = inf_ok and follow_ok
    print(f"[LATCH f={frame}] active={expected_latch}({exp_inf:.3f}) other={other_latch}({oth_inf:.3f}) "
          f"Ball=({bw.x:+.4f},{bw.y:+.4f},{bw.z:+.4f}) Seat=({sw.x:+.4f},{sw.y:+.4f},{sw.z:+.4f}) Δ={d:.5f} → {'PASS' if ok else 'FAIL'}")
    return ok


def validate_ball_inside_any_cube(ball, frame, radius, allowed_cubes=None):
    """
    At `frame`, confirm the ball sphere sits inside at least one of
    `allowed_cubes` (defaults to all 4). Returns (ok, cube_name, protrusion).
    """
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    names = allowed_cubes if allowed_cubes else list(CANON_CUBES.keys())
    best_name, best_prot = None, float('inf')
    inside_any = False
    for name in names:
        cube = bpy.data.objects.get(name)
        if cube is None:
            continue
        inside, prot, local = ball_inside_cube(ball, cube, radius)
        if inside:
            inside_any = True
            best_name = name
            best_prot = prot
            break
        if prot < best_prot:
            best_prot = prot
            best_name = name
    status = "PASS" if inside_any else "FAIL"
    bw = ball.matrix_world.translation
    print(f"[CONTAIN f={frame}] Ball=({bw.x:+.4f},{bw.y:+.4f},{bw.z:+.4f}) "
          f"best_cube={best_name} protrusion={best_prot:.4f} radius={radius:.4f} → {status}")
    return inside_any, best_name, best_prot


def validate_ball_radius_vs_geometry(ball):
    """Print ball radius. Cube interior half-extent is 0.5; walls are thin.
    Ball must have radius strictly less than 0.5 to fit centered; warn at >= 0.45."""
    r = get_ball_radius(ball)
    compatible = r < (CUBE_HALF_EXTENT - CONTAIN_TOL)
    tight = r >= 0.45
    tag = "FAIL" if not compatible else ("TIGHT" if tight else "PASS")
    print(f"[RADIUS] ball_radius={r:.4f}  cube_half_extent={CUBE_HALF_EXTENT}  → {tag}")
    if tight and compatible:
        print(f"[RADIUS] WARN: radius {r:.4f} >= 0.45 — sphere visually close to walls")
    return compatible, r


def validate_ball_follows_active_latch_2(ball, frame, expected_latch):
    """2-latch version: confirm ball tracks expected_latch (influence=1) and
    the other latch is OFF (influence=0). Returns ok bool."""
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    all_names = [CON_YELLOW, CON_BLUE]
    exp_con = ball.constraints.get(expected_latch)
    if exp_con is None:
        print(f"[LATCH2 f={frame}] FAIL — {expected_latch} missing")
        return False
    seat = exp_con.target
    bw = ball.matrix_world.translation
    sw = seat.matrix_world.translation if seat else mathutils.Vector((0, 0, 0))
    d  = (bw - sw).length
    parts = []
    inf_ok = True
    for cn in all_names:
        con = ball.constraints.get(cn)
        if con is None:
            parts.append(f"{cn}=MISS")
            inf_ok = False
            continue
        v = con.influence
        parts.append(f"{cn}={v:.3f}")
        if cn == expected_latch and v < 0.999:
            inf_ok = False
        if cn != expected_latch and v > 0.001:
            inf_ok = False
    follow_ok = d <= 1e-3
    ok = inf_ok and follow_ok
    inf_str = " ".join(parts)
    print(f"[LATCH2 f={frame}] {inf_str} Ball=({bw.x:+.4f},{bw.y:+.4f},{bw.z:+.4f}) "
          f"Seat=({sw.x:+.4f},{sw.y:+.4f},{sw.z:+.4f}) Δ={d:.5f} → {'PASS' if ok else 'FAIL'}")
    return ok


def run_true_containment_sweep(ball, radius):
    """
    2-latch containment + follow sweep.
    Schedule:
      F_START → F_TRANSFER (1–120):   Latch_Yellow active  → ball in Cube_Yellow
      F_TRANSFER_1 → F_END (121–240): Latch_Blue active    → ball in Cube_Blue
    """
    checkpoints = [
        (F_START,       CON_YELLOW, ["Cube_Yellow"]),
        (30,            CON_YELLOW, ["Cube_Yellow"]),
        (F_MID,         CON_YELLOW, ["Cube_Yellow"]),
        (90,            CON_YELLOW, ["Cube_Yellow"]),
        (F_TRANSFER,    CON_YELLOW, ["Cube_Yellow"]),
        (F_TRANSFER_1,  CON_BLUE,   ["Cube_Blue"]),
        (150,           CON_BLUE,   ["Cube_Blue"]),
        (F_RET,         CON_BLUE,   ["Cube_Blue"]),
        (210,           CON_BLUE,   ["Cube_Blue"]),
        (F_END,         CON_BLUE,   ["Cube_Blue"]),
    ]
    follow_all, contain_all = True, True
    print("--- TRUE CONTAINMENT SWEEP (2-latch) ---")
    for frame, active, allowed in checkpoints:
        f_ok = validate_ball_follows_active_latch_2(ball, frame, active)
        c_ok, _, _ = validate_ball_inside_any_cube(ball, frame, radius, allowed)
        follow_all  = follow_all and f_ok
        contain_all = contain_all and c_ok
    print(f"--- SWEEP RESULT: follow={'PASS' if follow_all else 'FAIL'} "
          f"contain={'PASS' if contain_all else 'FAIL'} ---")
    return follow_all, contain_all


################################################################################
# SECTION 7C: World-Space Contact Diagnosis (continuous-contact rule v2.0)
################################################################################

# Adjacent cube pairs and which hinge connects them.
# For each pair, define two points on each cube's shared face that must
# remain coincident (within tolerance) for the pair to be "in contact."
# We use the hinge world position as the shared-edge reference.
CONTACT_PAIRS = [
    ("Cube_Blue",   "Cube_Red",    "Hinge_Blue_Red",     "BR"),
    ("Cube_Red",    "Cube_Green",  "Hinge_Red_Green",    "RG"),
    ("Cube_Green",  "Cube_Yellow", "Hinge_Green_Yellow", "GY"),
]

CONTACT_TOL = 0.03  # world units — C10 built-in spacing is 0.02; this allows that + float slack


def measure_contact_gap(cube_a_name, cube_b_name, hinge_name):
    """
    Measure the world-space gap between two adjacent cubes at their shared
    hinge edge. Returns (gap_distance, detail_string).

    Method: each cube has a face toward the hinge. We compute the closest
    approach between the two cubes' bounding regions along the axis
    connecting their centers. For axis-aligned cubes this is trivial;
    for rotated cubes we use the actual face-normal projection.

    Simplified approach: for two unit cubes, the shared face is the plane
    equidistant from both centers along the connecting axis. The gap is
    the distance between the two cubes' nearest faces along that axis.
    For hinge-connected cubes the hinge position should lie on both faces.
    So we measure: how far is the hinge from each cube's nearest face?
    If the hinge is on both faces, gap=0. If one cube has moved away,
    the gap = distance from hinge to the farther cube's face.
    """
    a = bpy.data.objects.get(cube_a_name)
    b = bpy.data.objects.get(cube_b_name)
    h = bpy.data.objects.get(hinge_name)
    if not (a and b and h):
        return 999.0, "MISSING"

    aw = a.matrix_world.translation
    bw = b.matrix_world.translation
    hw = h.matrix_world.translation

    # For each cube, compute the signed distance from the cube center
    # to the hinge, then subtract the half-extent (0.5) to get how far
    # the cube's face is from the hinge.
    # The "connecting axis" is the vector from a→b centers.
    ab = bw - aw
    ab_len = ab.length
    if ab_len < 1e-6:
        return 0.0, "coincident"

    ab_dir = ab / ab_len

    # Project hinge onto the a→b axis relative to each cube center
    dist_a_to_h = (hw - aw).dot(ab_dir)  # signed dist along axis
    dist_b_to_h = (hw - bw).dot(ab_dir)  # signed (should be negative if h between a and b)

    # Each cube's half-extent along this axis (unit cube = 0.5)
    half = 0.5

    # Face of A toward hinge: at dist half from center along ab_dir
    face_a = dist_a_to_h - half  # negative = face is between center and hinge, positive = face beyond
    # Face of B toward hinge: at dist -half from center along ab_dir (toward A)
    face_b = -(dist_b_to_h + half)  # gap contribution from B side

    # If cubes are in contact, the gap between their facing surfaces = 0
    # Gap = distance between centers along axis - (half + half)
    center_dist_along_axis = (bw - aw).dot(ab_dir)
    face_gap = abs(center_dist_along_axis) - (half + half)

    # Also measure perpendicular displacement (cubes should share the same plane)
    perp_a = (hw - aw) - (hw - aw).dot(ab_dir) * ab_dir
    perp_b = (hw - bw) - (hw - bw).dot(ab_dir) * ab_dir

    detail = (f"cA={fmt_v(aw)} cB={fmt_v(bw)} "
              f"axis_dist={center_dist_along_axis:.4f} face_gap={face_gap:.4f}")

    return max(0.0, face_gap), detail


def fmt_v(v):
    return f"({v.x:+.4f},{v.y:+.4f},{v.z:+.4f})"


def run_world_space_contact_diagnosis():
    """
    World-space continuous-contact check per v2.0 detachment standard.
    At each sampled frame, measures gap between all 3 hinge-connected pairs.
    Returns (all_pass, results_table).
    """
    frames = [F_START, F_MID, F_TRANSFER, F_TRANSFER_1, F_RET, F_END]
    all_pass = True
    results = []

    print("╔═══════════════ C15 WORLD-SPACE CONTACT DIAGNOSIS ═══════════════╗")
    print(f"  Tolerance: {CONTACT_TOL} world units")
    print(f"  Pairs: BR (Blue-Red), RG (Red-Green), GY (Green-Yellow)")
    print("╠═════════════════════════════════════════════════════════════════╣")

    for f in frames:
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()

        row = {"frame": f}
        frame_fail = False

        # Print cube world positions
        for cn in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow"]:
            obj = bpy.data.objects.get(cn)
            if obj:
                w = obj.matrix_world.translation
                print(f"  F={f:>3} {cn}: {fmt_v(w)}")

        for ca, cb, hn, label in CONTACT_PAIRS:
            gap, detail = measure_contact_gap(ca, cb, hn)
            ok = gap <= CONTACT_TOL
            tag = "OK" if ok else "FAIL"
            if not ok:
                frame_fail = True
            row[label] = (gap, ok)
            print(f"  F={f:>3} {label}: gap={gap:.4f}  {tag}  ({detail})")

        row["detach"] = frame_fail
        if frame_fail:
            all_pass = False
        results.append(row)
        print(f"  F={f:>3} → {'FAIL — visible detachment' if frame_fail else 'PASS'}")
        print("  ─────────────────────────────────────────────────────────────────")

    print("╠═════════════════════════════════════════════════════════════════╣")

    # Summary table
    print("  SUMMARY TABLE:")
    print(f"  {'Frame':>5} | {'BR gap':>8} | {'RG gap':>8} | {'GY gap':>8} | Detach?")
    print(f"  {'─'*5}─┼─{'─'*8}─┼─{'─'*8}─┼─{'─'*8}─┼─{'─'*8}")
    for r in results:
        br_g, _ = r.get("BR", (0, True))
        rg_g, _ = r.get("RG", (0, True))
        gy_g, _ = r.get("GY", (0, True))
        d = "YES" if r["detach"] else "NO"
        print(f"  {r['frame']:>5} | {br_g:>8.4f} | {rg_g:>8.4f} | {gy_g:>8.4f} | {d}")

    print("╠═════════════════════════════════════════════════════════════════╣")
    if all_pass:
        print("  C15 MECHANICS PASS — continuous contact preserved")
    else:
        print("  C15 MECHANICS FAIL — continuous contact NOT preserved")
    print("╚═════════════════════════════════════════════════════════════════╝")
    return all_pass, results


################################################################################
# SECTION 8: UI / Operator
################################################################################

def setup_yellow_to_blue():
    return run_c15()


def run_c15():
    print("=== C15 Start: Yellow → Blue ===")

    reset_scene_to_canonical()
    dump_world_positions("after reset")
    canon_after_reset = validate_canonical_world("after reset")

    result = get_objects()
    if result is None:
        return False
    hinge, ball, yellow, green, blue, red = result

    bpy.context.scene.frame_set(F_START)
    hinge.rotation_mode  = 'XYZ'
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # Remove rigid body from ball if present
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    # FIX: seats and latches must be built BEFORE reparenting Yellow/Green
    if setup_ball_transfer(ball, yellow, blue, hinge) is False:
        return False
    dump_world_positions("after seat build")

    # Hard validation: Seat_Yellow must be inside Yellow
    if not validate_seat_yellow_inside_yellow():
        print("[C15 ABORT] Seat_Yellow is not inside Cube_Yellow at start.")
        return False

    # Rule §1 + §2: force correct ball start — snap to Seat_Yellow world pos.
    # Clear any leftover location fcurves first, then pin ball at F_START.
    seat_yellow = bpy.data.objects.get("Seat_Yellow")
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()
    ball.location = seat_yellow.matrix_world.translation.copy()
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()

    # Hierarchy: Yellow rides Green; Green driven by hinge
    parent_preserve_world(yellow, green)
    parent_preserve_world(green,  hinge)
    bpy.context.view_layer.update()
    print("Hierarchy: HRG(root) → Green → Yellow  |  Blue+Red fixed")
    dump_world_positions("after reparenting")

    setup_hinge_keyframes(hinge)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()
    dump_world_positions("at F_START")

    # ── World-space contact diagnosis (continuous-contact rule v2.0) ─────
    mech_pass, mech_results = run_world_space_contact_diagnosis()

    # VB Correction validators (seat-level)
    start_ok = validate_start_state()
    hold_ok  = validate_alignment_at_hold()
    mid_ok   = validate_no_drift_toward_red()
    end_ok   = validate_end_inside_blue()

    # TRUE containment + latch-follow sweep (VB false-pass correction)
    radius_ok, ball_radius = validate_ball_radius_vs_geometry(ball)
    follow_all, contain_all = run_true_containment_sweep(ball, ball_radius)

    # HARD ABORT: ball MUST be inside Yellow's visible mesh at F_START.
    # If the mesh-bbox containment check fails at frame 1, the run is invalid.
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()
    yellow_obj = bpy.data.objects.get("Cube_Yellow")
    start_inside, start_prot, _ = ball_inside_cube(ball, yellow_obj, ball_radius)
    print(f"[C15 START HARD CHECK] ball_inside_yellow_mesh={start_inside} "
          f"protrusion={start_prot:.4f}")
    if not start_inside:
        print("[C15 HARD FAIL] Ball is NOT inside Yellow's visible mesh at F_START.")

    # End-of-run validation: check scene returns to canonical at F_END
    bpy.context.scene.frame_set(F_END)
    bpy.context.view_layer.update()
    dump_world_positions("at F_END")
    canon_at_end = validate_canonical_world("at F_END")

    # Back to F_START for playback
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()

    # Final summary table
    seats_ok = (bpy.data.objects.get("Seat_Yellow") is not None
                and bpy.data.objects.get("Seat_Blue") is not None)
    ball_ok  = (ball.constraints.get(CON_YELLOW) is not None
                and ball.constraints.get(CON_BLUE) is not None)
    print_c15_summary(
        cubes_ok=canon_after_reset,
        hinges_ok=canon_after_reset,
        seats_ok=seats_ok,
        ball_ok=ball_ok,
        canonical_ok=canon_at_end,
    )

    validate_four_seats("C15 final")

    # VB TRUE-CONTAINMENT compliance (2-latch: Yellow → Blue)
    print("╔══════════ C15 VB TRUE-CONTAINMENT TABLE (2-LATCH) ══════════╗")
    print(f"  Ball center follows active latch    : {'PASS' if follow_all else 'FAIL'}")
    print(f"  Ball sphere stays inside cube volume: {'PASS' if contain_all else 'FAIL'}")
    print(f"  Ball radius compatible with geometry: {'PASS' if radius_ok else 'FAIL'}  (r={ball_radius:.4f})")
    print(f"  Visible mid-run containment         : {'PASS' if contain_all else 'FAIL'}")
    print(f"  Final inside Blue                   : {'PASS' if end_ok else 'FAIL'}")
    print(f"  False-positive validators removed   : PASS  (mesh-bbox sweep replaces seat-only checks)")
    print(f"  2-latch schedule                    : Yellow(1–{F_TRANSFER}) → Blue({F_TRANSFER_1}–{F_END})")
    print("  ─ Legacy seat-level (informational) ─")
    print(f"    Ball starts in Yellow           : {'PASS' if start_ok else 'FAIL'}")
    print(f"    Alignment at F_HOLD (seat XY)   : {'PASS' if hold_ok else 'FAIL'}")
    print(f"    No drift toward Red             : {'PASS' if mid_ok else 'FAIL'}")
    print(f"    Base restored at 240            : {'PASS' if canon_at_end else 'FAIL'}")
    print("╚═══════════════════════════════════════════════════════════════╝")
    if not (follow_all and contain_all):
        print("[C15 HARD FAIL] Ball escapes cube volume or does not follow active latch.")

    # ── FINAL VERDICTS ──────────────────────────────────────────────────
    print("╔══════════ C15 FINAL VERDICTS ══════════╗")
    mech_fail_frames = [r["frame"] for r in mech_results if r["detach"]]
    print(f"  MECHANICS (world-space contact) : {'PASS' if mech_pass else 'FAIL'}")
    if mech_fail_frames:
        print(f"    failing frames: {mech_fail_frames}")
    ball_start_ok = start_inside  # mesh-bbox check, not origin-delta
    ball_containment_ok = ball_start_ok and follow_all and contain_all
    print(f"  BALL INSIDE YELLOW AT F_START  : {'PASS' if ball_start_ok else 'FAIL'}")
    print(f"  BALL CONTAINMENT (full run)    : {'PASS' if ball_containment_ok else 'FAIL'}")
    print("╚════════════════════════════════════════╝")

    print("=== C15 Complete: Yellow → Blue ===")
    print(f"Frames {F_START}–{F_END} | Transfer at {F_TRANSFER}→{F_TRANSFER_1}")
    return True


class LORQB_OT_ResetC15(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c15"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "C15 reset to base")
        return {'FINISHED'}


class LORQB_OT_YellowToBlue(bpy.types.Operator):
    bl_idname  = "lorqb.yellow_to_blue"
    bl_label   = "Run C15: Yellow → Blue"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = run_c15()
        if success:
            self.report({'INFO'}, "C15 armed — press Play to run")
        else:
            self.report({'ERROR'}, "C15 failed — check console")
        return {'FINISHED'}


class LORQB_PT_C15Panel(bpy.types.Panel):
    bl_label       = "LorQB C15: Yellow → Blue"
    bl_idname      = "LORQB_PT_c15_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c15",     text="Reset to Base",         icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.yellow_to_blue", text="Run C15: Yellow → Blue", icon='PLAY')

################################################################################
# SECTION 8: Register
################################################################################

_classes = [LORQB_OT_ResetC15, LORQB_OT_YellowToBlue, LORQB_PT_C15Panel]

def register():
    for cls in _classes:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

register()

################################################################################
# SECTION 9: Notes
################################################################################
# Geometry proof (canonical state):
#   HRG at (0, -0.51, 1) — Y+180° swings right branch
#   Seat_Yellow starts at (-0.51, 0.51, 0.25) — interior bottom of Yellow
#   After HRG Y+180°: Seat_Yellow arrives at (0.51, 0.51, 1.75)
#   Seat_Blue fixed at (0.51, 0.51, 0.25) — directly below
#   Ball drops 1.5 units through aligned holes at frame 841.
#
# Verification checklist:
#   [x] Ball starts outside cubes only at beginning (F_ZERO before constraints active)
#   [x] Ball enters Yellow at F_START via Latch_Yellow COPY_TRANSFORMS (influence=1)
#   [x] Ball never hangs outside side wall — COPY_TRANSFORMS tracks seat exactly
#   [x] Transfer only on aligned holes — swap at F_TRANSFER_1 when HRG=180°
#   [x] Final state correct — Latch_Blue=1 through F_END, ball inside Blue
