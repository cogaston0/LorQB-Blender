# ============================================================================
# T03_validation_agent.py
# Validates T03_red_to_yellow.py against intended behavior.
# Run this in Blender's Text Editor AFTER running T03_red_to_yellow.py.
# ============================================================================

import bpy
import math
import mathutils

PASS  = "✅ PASS"
FAIL  = "❌ FAIL"
WARN  = "⚠️  WARN"
INFO  = "ℹ️  INFO"

results = []

def check(label, condition, detail="", level="check"):
    status = PASS if condition else FAIL
    msg = f"{status} | {label}"
    if detail:
        msg += f"  →  {detail}"
    results.append((condition, msg))
    print(msg)
    return condition

def warn(label, detail=""):
    msg = f"{WARN} | {label}"
    if detail:
        msg += f"  →  {detail}"
    results.append((None, msg))
    print(msg)

def info(label, detail=""):
    msg = f"{INFO} | {label}"
    if detail:
        msg += f"  →  {detail}"
    results.append((None, msg))
    print(msg)

print("\n" + "="*70)
print("T03 VALIDATION AGENT — Red → Yellow")
print("="*70 + "\n")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION A: Required Objects Exist
# ─────────────────────────────────────────────────────────────────────────────
print("── A: Required Objects ──")

required = [
    "Ball", "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
    "Hinge_Green_Yellow", "T3_Assembly",
    "Seat_Red_Start", "Seat_Yellow_Side",
]
all_present = True
for name in required:
    obj = bpy.data.objects.get(name)
    ok = check(f"Object exists: {name}", obj is not None)
    if not ok:
        all_present = False

if not all_present:
    print("\nCRITICAL: Missing objects — remaining checks may be unreliable.\n")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION B: Hierarchy Validation
# ─────────────────────────────────────────────────────────────────────────────
print("\n── B: Hierarchy ──")

def get_parent_name(obj_name):
    obj = bpy.data.objects.get(obj_name)
    if obj and obj.parent:
        return obj.parent.name
    return None

check("Cube_Blue   parent = T3_Assembly",  get_parent_name("Cube_Blue")   == "T3_Assembly",
      f"actual: {get_parent_name('Cube_Blue')}")
check("Cube_Red    parent = T3_Assembly",  get_parent_name("Cube_Red")    == "T3_Assembly",
      f"actual: {get_parent_name('Cube_Red')}")
check("Cube_Green  parent = T3_Assembly",  get_parent_name("Cube_Green")  == "T3_Assembly",
      f"actual: {get_parent_name('Cube_Green')}")
check("Hinge_GY    parent = Cube_Green",   get_parent_name("Hinge_Green_Yellow") == "Cube_Green",
      f"actual: {get_parent_name('Hinge_Green_Yellow')}")
check("Cube_Yellow parent = Hinge_GY",     get_parent_name("Cube_Yellow") == "Hinge_Green_Yellow",
      f"actual: {get_parent_name('Cube_Yellow')}")

# Seat parents
check("Seat_Red_Start  parent = Cube_Red",    get_parent_name("Seat_Red_Start")   == "Cube_Red",
      f"actual: {get_parent_name('Seat_Red_Start')}")
check("Seat_Yellow_Side parent = Cube_Yellow", get_parent_name("Seat_Yellow_Side") == "Cube_Yellow",
      f"actual: {get_parent_name('Seat_Yellow_Side')}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION C: Ball Constraints
# ─────────────────────────────────────────────────────────────────────────────
print("\n── C: Ball Constraints ──")

ball = bpy.data.objects.get("Ball")
if ball:
    con_names = [c.name for c in ball.constraints]
    info("Ball constraints found", str(con_names))

    latch_red    = ball.constraints.get("Latch_Red_Start")
    latch_yellow = ball.constraints.get("Latch_Yellow_Side")

    check("Latch_Red_Start exists",    latch_red    is not None)
    check("Latch_Yellow_Side exists",  latch_yellow is not None)

    if latch_red:
        check("Latch_Red_Start type = COPY_TRANSFORMS",
              latch_red.type == 'COPY_TRANSFORMS',
              f"actual: {latch_red.type}")
        check("Latch_Red_Start target = Seat_Red_Start",
              latch_red.target is not None and latch_red.target.name == "Seat_Red_Start",
              f"actual: {latch_red.target.name if latch_red.target else 'None'}")

    if latch_yellow:
        check("Latch_Yellow_Side type = COPY_TRANSFORMS",
              latch_yellow.type == 'COPY_TRANSFORMS',
              f"actual: {latch_yellow.type}")
        check("Latch_Yellow_Side target = Seat_Yellow_Side",
              latch_yellow.target is not None and latch_yellow.target.name == "Seat_Yellow_Side",
              f"actual: {latch_yellow.target.name if latch_yellow.target else 'None'}")
else:
    warn("Ball not found — constraint checks skipped")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION D: Constraint Influence Keyframes at Critical Frames
# ─────────────────────────────────────────────────────────────────────────────
print("\n── D: Constraint Influence Keyframes ──")

def get_influence_at_frame(obj, con_name, frame):
    """Evaluate constraint influence at a specific frame."""
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return None
    try:
        fcurves = obj.animation_data.action.layers[0].strips[0].channelbags[0].fcurves
    except Exception:
        return None
    data_path = f'constraints["{con_name}"].influence'
    for fc in fcurves:
        if fc.data_path == data_path:
            return fc.evaluate(frame)
    return None

if ball:
    # Latch_Red_Start: 1.0 at frame 1, 1.0 at frame 160, 0.0 at frame 161
    r_f1   = get_influence_at_frame(ball, "Latch_Red_Start",   1)
    r_f160 = get_influence_at_frame(ball, "Latch_Red_Start",   160)
    r_f161 = get_influence_at_frame(ball, "Latch_Red_Start",   161)

    check("Latch_Red_Start  influence @ frame 1   = 1.0",
          r_f1 is not None and abs(r_f1 - 1.0) < 0.01,
          f"actual: {round(r_f1, 4) if r_f1 is not None else 'N/A'}")
    check("Latch_Red_Start  influence @ frame 160 = 1.0",
          r_f160 is not None and abs(r_f160 - 1.0) < 0.01,
          f"actual: {round(r_f160, 4) if r_f160 is not None else 'N/A'}")
    check("Latch_Red_Start  influence @ frame 161 = 0.0",
          r_f161 is not None and abs(r_f161 - 0.0) < 0.01,
          f"actual: {round(r_f161, 4) if r_f161 is not None else 'N/A'}")

    # Latch_Yellow_Side: 0.0 at frame 1, 0.0 at frame 160, 1.0 at frame 161
    y_f1   = get_influence_at_frame(ball, "Latch_Yellow_Side", 1)
    y_f160 = get_influence_at_frame(ball, "Latch_Yellow_Side", 160)
    y_f161 = get_influence_at_frame(ball, "Latch_Yellow_Side", 161)

    check("Latch_Yellow_Side influence @ frame 1   = 0.0",
          y_f1 is not None and abs(y_f1 - 0.0) < 0.01,
          f"actual: {round(y_f1, 4) if y_f1 is not None else 'N/A'}")
    check("Latch_Yellow_Side influence @ frame 160 = 0.0",
          y_f160 is not None and abs(y_f160 - 0.0) < 0.01,
          f"actual: {round(y_f160, 4) if y_f160 is not None else 'N/A'}")
    check("Latch_Yellow_Side influence @ frame 161 = 1.0",
          y_f161 is not None and abs(y_f161 - 1.0) < 0.01,
          f"actual: {round(y_f161, 4) if y_f161 is not None else 'N/A'}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION E: Hinge_Green_Yellow Rotation Keyframes
# ─────────────────────────────────────────────────────────────────────────────
print("\n── E: Hinge_Green_Yellow Rotation Keyframes ──")

def get_rot_at_frame(obj, axis, frame):
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return None
    try:
        fcurves = obj.animation_data.action.layers[0].strips[0].channelbags[0].fcurves
    except Exception:
        return None
    for fc in fcurves:
        if fc.data_path == "rotation_euler" and fc.array_index == axis:
            return math.degrees(fc.evaluate(frame))
    return None

hinge_gy = bpy.data.objects.get("Hinge_Green_Yellow")
if hinge_gy:
    HGY_AXIS    = 0     # X
    HGY_DEGREES = 180.0

    r1   = get_rot_at_frame(hinge_gy, HGY_AXIS, 1)
    r80  = get_rot_at_frame(hinge_gy, HGY_AXIS, 80)
    r200 = get_rot_at_frame(hinge_gy, HGY_AXIS, 200)
    r240 = get_rot_at_frame(hinge_gy, HGY_AXIS, 240)

    check("HGY rotation @ frame 1   =   0°",
          r1   is not None and abs(r1)            < 1.0, f"actual: {round(r1,2) if r1 is not None else 'N/A'}°")
    check("HGY rotation @ frame 80  = 180°",
          r80  is not None and abs(r80  - HGY_DEGREES) < 1.0, f"actual: {round(r80,2) if r80 is not None else 'N/A'}°")
    check("HGY rotation @ frame 200 = 180°",
          r200 is not None and abs(r200 - HGY_DEGREES) < 1.0, f"actual: {round(r200,2) if r200 is not None else 'N/A'}°")
    check("HGY rotation @ frame 240 =   0°",
          r240 is not None and abs(r240)           < 1.0, f"actual: {round(r240,2) if r240 is not None else 'N/A'}°")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION F: T3_Assembly Rotation Keyframes
# ─────────────────────────────────────────────────────────────────────────────
print("\n── F: T3_Assembly Rotation Keyframes ──")

assembly = bpy.data.objects.get("T3_Assembly")
if assembly:
    ASSEMBLY_AXIS    = 1    # Y
    ASSEMBLY_DEGREES = 90.0

    a1   = get_rot_at_frame(assembly, ASSEMBLY_AXIS, 1)
    a80  = get_rot_at_frame(assembly, ASSEMBLY_AXIS, 80)
    a160 = get_rot_at_frame(assembly, ASSEMBLY_AXIS, 160)
    a161 = get_rot_at_frame(assembly, ASSEMBLY_AXIS, 161)
    a200 = get_rot_at_frame(assembly, ASSEMBLY_AXIS, 200)
    a240 = get_rot_at_frame(assembly, ASSEMBLY_AXIS, 240)

    check("Assembly Y-rot @ frame 1   =  0°",
          a1   is not None and abs(a1)                   < 1.0, f"actual: {round(a1,2) if a1 is not None else 'N/A'}°")
    check("Assembly Y-rot @ frame 80  =  0°",
          a80  is not None and abs(a80)                  < 1.0, f"actual: {round(a80,2) if a80 is not None else 'N/A'}°")
    check("Assembly Y-rot @ frame 160 = 90°",
          a160 is not None and abs(a160 - ASSEMBLY_DEGREES) < 1.0, f"actual: {round(a160,2) if a160 is not None else 'N/A'}°")
    check("Assembly Y-rot @ frame 161 = 90°",
          a161 is not None and abs(a161 - ASSEMBLY_DEGREES) < 1.0, f"actual: {round(a161,2) if a161 is not None else 'N/A'}°")
    check("Assembly Y-rot @ frame 200 =  0°",
          a200 is not None and abs(a200)                 < 1.0, f"actual: {round(a200,2) if a200 is not None else 'N/A'}°")
    check("Assembly Y-rot @ frame 240 =  0°",
          a240 is not None and abs(a240)                 < 1.0, f"actual: {round(a240,2) if a240 is not None else 'N/A'}°")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION G: Seat_Red_Start — Not Hardcoded Check
# ─────────────────────────────────────────────────────────────────────────────
print("\n── G: Seat_Red_Start Runtime Capture Check ──")

seat_rs = bpy.data.objects.get("Seat_Red_Start")
ball    = bpy.data.objects.get("Ball")
if seat_rs and ball:
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    ball_world = ball.matrix_world.translation
    seat_world = seat_rs.matrix_world.translation
    dist = (ball_world - seat_world).length
    check("Seat_Red_Start world pos matches Ball @ frame 1 (runtime capture)",
          dist < 0.01,
          f"distance: {round(dist, 5)}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION H: Scene Frame Range
# ─────────────────────────────────────────────────────────────────────────────
print("\n── H: Scene Frame Range ──")

check("Scene frame_start = 1",   bpy.context.scene.frame_start == 1,
      f"actual: {bpy.context.scene.frame_start}")
check("Scene frame_end   = 240", bpy.context.scene.frame_end   == 240,
      f"actual: {bpy.context.scene.frame_end}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION I: Open TODO Flags
# ─────────────────────────────────────────────────────────────────────────────
print("\n── I: Open TODO Flags (require manual verification in Blender) ──")

warn("TODO: HGY_AXIS (X=0) — verify side-hole exposure axis in Blender viewport")
warn("TODO: HGY_SIGN (+1.0) — verify rotation direction exposes Yellow side hole")
warn("TODO: ASSEMBLY_SIGN (+1.0) — verify Y-swing brings Red above Yellow side hole")
warn("TODO: SEAT_YELLOW_SIDE_WORLD (-0.51, 0.0, 0.25) — verify exact world coord in Blender")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION J: Blender 5.0.1 API Compliance
# ─────────────────────────────────────────────────────────────────────────────
print("\n── J: Blender 5.0.1 API — fcurves Access ──")

def check_fcurves_api(obj_name):
    obj = bpy.data.objects.get(obj_name)
    if not obj or not obj.animation_data or not obj.animation_data.action:
        warn(f"{obj_name}: no animation data to check API on")
        return
    try:
        fcurves = obj.animation_data.action.layers[0].strips[0].channelbags[0].fcurves
        check(f"{obj_name} fcurves accessible via Blender 5.0.1 API path",
              len(fcurves) > 0,
              f"{len(fcurves)} fcurves found")
    except Exception as e:
        check(f"{obj_name} fcurves accessible via Blender 5.0.1 API path", False, str(e))

check_fcurves_api("Ball")
check_fcurves_api("Hinge_Green_Yellow")
check_fcurves_api("T3_Assembly")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

passed  = sum(1 for ok, _ in results if ok is True)
failed  = sum(1 for ok, _ in results if ok is False)
warnings = sum(1 for ok, _ in results if ok is None)

print(f"  ✅ PASSED  : {passed}")
print(f"  ❌ FAILED  : {failed}")
print(f"  ⚠️  WARNINGS: {warnings}")
print("="*70)

if failed == 0:
    print("✅ T03 is structurally valid. Verify TODO flags manually in Blender.")
else:
    print("❌ Issues found. Review FAILED items above before running in Blender.")
print()