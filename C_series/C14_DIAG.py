# ============================================================================
# C14_DIAG.py  (Blender 5.1.1)
# C14 Diagnostic — paste into Blender Text Editor and Alt+P
# Run AFTER C14_green_to_yellow.py has been run (Alt+P on C14 first).
# Checks parent chain, world positions, ball location, constraints, frame range.
# ============================================================================

import bpy
import math
import mathutils

PASS = "✓"
FAIL = "✗"
TOL  = 0.02

def wpos(name):
    o = bpy.data.objects.get(name)
    if not o: return None
    bpy.context.view_layer.update()
    return tuple(round(v, 3) for v in o.matrix_world.translation)

def rot_deg(name):
    o = bpy.data.objects.get(name)
    if not o: return None
    return tuple(round(math.degrees(v), 1) for v in o.rotation_euler)

def near(a, b):
    if a is None or b is None: return False
    return all(abs(x - y) < TOL for x, y in zip(a, b))

def check(label, ok, got=None, expected=None):
    sym = PASS if ok else FAIL
    line = f"  {sym} {label}"
    if not ok and got is not None:
        line += f"\n       got={got}  expected={expected}"
    print(line)
    return ok

results = []

print("\n" + "=" * 60)
print("C14 DIAGNOSTIC")
print("=" * 60)

################################################################################
print("\n[1] OBJECTS EXIST")
for name in ["Ball", "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
             "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
    ok = bpy.data.objects.get(name) is not None
    results.append(check(name, ok, got="MISSING" if not ok else None))

################################################################################
print("\n[2] PARENT CHAIN")
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
chain = [
    ("Cube_Green",      "Hinge_Green_Yellow"),
    ("Hinge_Red_Green", "Cube_Green"),
    ("Cube_Red",        "Hinge_Red_Green"),
    ("Hinge_Blue_Red",  "Cube_Red"),
    ("Cube_Blue",       "Hinge_Blue_Red"),
]
for child_n, parent_n in chain:
    o = bpy.data.objects.get(child_n)
    actual = o.parent.name if o and o.parent else "None"
    ok = actual == parent_n
    results.append(check(f"{child_n}.parent == {parent_n}", ok,
                         got=actual, expected=parent_n))

################################################################################
print("\n[3] WORLD POSITIONS at frame 1")
canonical = {
    "Cube_Blue":          ( 0.51,  0.51, 0.25),
    "Cube_Red":           ( 0.51, -0.51, 0.25),
    "Cube_Green":         (-0.51, -0.51, 0.25),
    "Cube_Yellow":        (-0.51,  0.51, 0.25),
    "Hinge_Blue_Red":     ( 0.51,  0.0,  1.0),
    "Hinge_Red_Green":    ( 0.0,  -0.51, 1.0),
    "Hinge_Green_Yellow": (-0.51,  0.0,  1.0),
}
for name, exp in canonical.items():
    actual = wpos(name)
    ok = near(actual, exp)
    results.append(check(f"{name} at {exp}", ok, got=actual, expected=exp))

################################################################################
print("\n[4] BALL POSITION at frame 1")
ball_pos = wpos("Ball")
exp_ball = (-0.51, -0.51, 0.25)
ok = near(ball_pos, exp_ball)
results.append(check(f"Ball inside Green {exp_ball}", ok,
                     got=ball_pos, expected=exp_ball))
print(f"       Ball actual: {ball_pos}")

################################################################################
print("\n[5] HINGE ROTATIONS at frame 1")
for h in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
    rot = rot_deg(h)
    ok = rot == (0.0, 0.0, 0.0)
    results.append(check(f"{h} rotation == (0,0,0)", ok,
                         got=rot, expected=(0.0, 0.0, 0.0)))

################################################################################
print("\n[6] BALL CONSTRAINTS")
ball = bpy.data.objects.get("Ball")
if ball:
    names = [c.name for c in ball.constraints]
    print(f"  Constraints present: {names}")
    results.append(check("Latch_Green exists", "Latch_Green" in names))
    results.append(check("Latch_Yellow exists", "Latch_Yellow" in names))
    if "Latch_Green" in names:
        c = ball.constraints["Latch_Green"]
        results.append(check("Latch_Green type == COPY_TRANSFORMS",
                             c.type == 'COPY_TRANSFORMS', got=c.type))
    if "Latch_Yellow" in names:
        c = ball.constraints["Latch_Yellow"]
        results.append(check("Latch_Yellow type == COPY_TRANSFORMS",
                             c.type == 'COPY_TRANSFORMS', got=c.type))
else:
    results.append(check("Ball exists", False))

################################################################################
print("\n[7] INERT HINGES (no animation on RG / BR)")
hinge_rg = bpy.data.objects.get("Hinge_Red_Green")
hinge_br = bpy.data.objects.get("Hinge_Blue_Red")
results.append(check("Hinge_Red_Green has NO animation data",
                     hinge_rg is None or hinge_rg.animation_data is None,
                     got="HAS animation" if hinge_rg and hinge_rg.animation_data else None))
results.append(check("Hinge_Blue_Red has NO animation data",
                     hinge_br is None or hinge_br.animation_data is None,
                     got="HAS animation" if hinge_br and hinge_br.animation_data else None))

################################################################################
print("\n[8] FRAME RANGE")
fs = bpy.context.scene.frame_start
fe = bpy.context.scene.frame_end
results.append(check(f"frame_start == 1", fs == 1, got=fs, expected=1))
results.append(check(f"frame_end == 240", fe == 240, got=fe, expected=240))

################################################################################
print("\n[9] SEAT POSITIONS at frame 1")
seat_g = bpy.data.objects.get("Seat_Green")
seat_y = bpy.data.objects.get("Seat_Yellow")
if seat_g:
    sg_pos = wpos("Seat_Green")
    exp_sg = (-0.51, -0.51, 0.25)
    ok = near(sg_pos, exp_sg)
    results.append(check(f"Seat_Green world near {exp_sg}", ok,
                         got=sg_pos, expected=exp_sg))
else:
    results.append(check("Seat_Green exists", False, got="MISSING"))

if seat_y:
    sy_pos = wpos("Seat_Yellow")
    exp_sy = (-0.51, 0.51, 0.25)
    ok = near(sy_pos, exp_sy)
    results.append(check(f"Seat_Yellow world near {exp_sy}", ok,
                         got=sy_pos, expected=exp_sy))
else:
    results.append(check("Seat_Yellow exists", False, got="MISSING"))

################################################################################
passed = sum(results)
total  = len(results)
print("\n" + "=" * 60)
print(f"RESULT: {passed}/{total} checks passed")
if passed == total:
    print("ALL CHECKS PASSED — C14 ready to test in viewport")
else:
    print(f"FAILED: {total - passed} issue(s) need fixing before testing")
print("=" * 60 + "\n")
print("ROT_SIGN = -1.0 still needs empirical viewport verification.")
print("Watch: at frame 60 Hinge_Green_Yellow should be at 90°")
print("       and Green should swing TOWARD Yellow (not away).")
