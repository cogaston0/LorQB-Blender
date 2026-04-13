# ============================================================================
# T04_scene_probe.py  (Blender 5.0.1)
# Run this in the Blender Text Editor BEFORE running any T04 script.
# It answers the three diagnostic questions exactly.
# Paste the full console output back to Claude.
# ============================================================================

import bpy
from mathutils import Vector

print("\n" + "="*60)
print("T04 SCENE PROBE")
print("="*60)

NAMES = ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
         "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow", "Ball"]

# --- Q1: World positions and parent chain for every object ---
print("\n[1] WORLD POSITIONS + PARENT CHAIN")
for name in NAMES:
    o = bpy.data.objects.get(name)
    if o is None:
        print(f"  {name}: MISSING")
        continue
    loc = o.matrix_world.translation
    parent = o.parent.name if o.parent else "None"
    print(f"  {name}: world=({loc.x:+.4f}, {loc.y:+.4f}, {loc.z:+.4f})  parent={parent}")

# --- Q2: Direction from Green to Red (tells us the axis) ---
print("\n[2] DIRECTION VECTORS BETWEEN CUBE PAIRS")
pairs = [
    ("Cube_Green", "Cube_Red"),
    ("Cube_Red",   "Cube_Blue"),
    ("Cube_Green", "Cube_Yellow"),
]
for a_name, b_name in pairs:
    a = bpy.data.objects.get(a_name)
    b = bpy.data.objects.get(b_name)
    if a is None or b is None:
        print(f"  {a_name} → {b_name}: one or both MISSING")
        continue
    delta = b.matrix_world.translation - a.matrix_world.translation
    print(f"  {a_name} → {b_name}: delta=({delta.x:+.4f}, {delta.y:+.4f}, {delta.z:+.4f})")

# --- Q3: Current frame and hinge rotations ---
print("\n[3] CURRENT FRAME + HINGE ROTATIONS")
scene = bpy.context.scene
print(f"  Current frame: {scene.frame_current}")
for name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
    o = bpy.data.objects.get(name)
    if o is None:
        print(f"  {name}: MISSING")
        continue
    r = o.rotation_euler
    print(f"  {name}: euler=({r.x:+.4f}, {r.y:+.4f}, {r.z:+.4f}) mode={o.rotation_mode}")

# --- Q4: Cube dimensions ---
print("\n[4] CUBE DIMENSIONS")
for name in ["Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow"]:
    o = bpy.data.objects.get(name)
    if o is None:
        print(f"  {name}: MISSING")
        continue
    d = o.dimensions
    print(f"  {name}: ({d.x:.4f}, {d.y:.4f}, {d.z:.4f})")

# --- Q5: Validation pass/fail at frame 1 ---
print("\n[5] ATTACHMENT DISTANCES AT CURRENT FRAME")
blue  = bpy.data.objects.get("Cube_Blue")
red   = bpy.data.objects.get("Cube_Red")
green = bpy.data.objects.get("Cube_Green")
if blue and red and green:
    d_br = (blue.matrix_world.translation - red.matrix_world.translation).length
    d_rg = (red.matrix_world.translation  - green.matrix_world.translation).length
    print(f"  Blue-Red distance:  {d_br:.6f}")
    print(f"  Red-Green distance: {d_rg:.6f}")
else:
    print("  Cannot compute — one or more cubes missing")

print("\n" + "="*60)
print("PROBE COMPLETE — paste full output to Claude")
print("="*60 + "\n")
