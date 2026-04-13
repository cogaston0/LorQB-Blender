# ============================================================================
# T04_no_detachment.py  (Blender 5.0.1)
# Mechanical-only T04 scaffold
#
# Goal:
# - NO DETACHMENT
# - Blue rotates first on Hinge_Blue_Red
# - Then Red+Blue move together on Hinge_Red_Green
# - No physics, no drivers, no armatures
#
# Expected object names in scene:
#   Cube_Blue
#   Cube_Red
#   Cube_Green
#   Cube_Yellow
#
# The script creates/reuses:
#   Hinge_Blue_Red
#   Hinge_Red_Green
#   Hinge_Green_Yellow
#
# IMPORTANT:
# - This script enforces the attachment logic.
# - If the diagonal direction is opposite in your scene, flip HRG_SIGN only.
# ============================================================================

import bpy
import math
from mathutils import Vector

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
F1   = 1
F80  = 80
F81  = 81
F160 = 160
F161 = 161
F200 = 200
F201 = 201
F240 = 240

# Blue first
HBR_DEG = 180.0

# Carry Red+Blue toward Green
# Z-axis +90° proven by geometry: HBR offset (0.51,0.51,0) from HRG
# Z+90° → (-0.51, 0.51, 0) → world (-0.51, 0, 1) = Green's position
HRG_DEG  = 90.0
HBR_SIGN = 1.0
HRG_SIGN = 1.0

# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def obj(name):
    o = bpy.data.objects.get(name)
    if o is None:
        raise RuntimeError(f"Missing required object: {name}")
    return o

def clear_anim(o):
    if o.animation_data:
        o.animation_data_clear()

def ensure_empty(name):
    o = bpy.data.objects.get(name)
    if o is None:
        o = bpy.data.objects.new(name, None)
        o.empty_display_type = 'PLAIN_AXES'
        o.empty_display_size = 0.18
        bpy.context.scene.collection.objects.link(o)
    return o

def clear_parent_keep_world(o):
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw

def parent_keep_world(child, parent):
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = mw

def top_z(o):
    return o.matrix_world.translation.z + (o.dimensions.z * 0.5)

def midpoint(a, b):
    return (a.matrix_world.translation + b.matrix_world.translation) * 0.5

def place_hinge_shared_top_edge(hinge, a, b):
    """
    General midpoint placement on the shared top edge region.
    Works from current cube world positions.
    """
    m = midpoint(a, b)
    hinge.location = Vector((m.x, m.y, max(top_z(a), top_z(b))))
    hinge.rotation_euler = (0.0, 0.0, 0.0)

def set_linear(o):
    ad = o.animation_data
    if not ad or not ad.action:
        return

    action = ad.action

    # Blender 5 layered actions compatibility
    if hasattr(action, "layers") and action.layers:
        for layer in action.layers:
            for strip in layer.strips:
                if hasattr(strip, "channelbags"):
                    for cb in strip.channelbags:
                        for fc in cb.fcurves:
                            for kp in fc.keyframe_points:
                                kp.interpolation = 'LINEAR'
        return

    # fallback
    if action.fcurves:
        for fc in action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

def insert_rot_x_deg(o, frame, deg):
    o.rotation_mode = 'XYZ'
    o.rotation_euler[0] = math.radians(deg)
    o.keyframe_insert(data_path="rotation_euler", index=0, frame=frame)

def insert_rot_z_deg(o, frame, deg):
    o.rotation_mode = 'XYZ'
    o.rotation_euler[2] = math.radians(deg)
    o.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)

def validate_no_origin_rotation(hbr, hrg):
    if hbr.location.length < 1e-6:
        raise RuntimeError("Hinge_Blue_Red is at world origin. Invalid hinge placement.")
    if hrg.location.length < 1e-6:
        raise RuntimeError("Hinge_Red_Green is at world origin. Invalid hinge placement.")

def validate_attachment_dist(a, b, expected, label):
    d = (a.matrix_world.translation - b.matrix_world.translation).length
    if abs(d - expected) > 1e-4:
        raise RuntimeError(
            f"{label} distance changed. Detachment likely. Expected {expected:.6f}, got {d:.6f}"
        )

# ----------------------------------------------------------------------------
# GET OBJECTS
# ----------------------------------------------------------------------------
blue   = obj("Cube_Blue")
red    = obj("Cube_Red")
green  = obj("Cube_Green")
yellow = obj("Cube_Yellow")

hbr = ensure_empty("Hinge_Blue_Red")
hrg = ensure_empty("Hinge_Red_Green")
hgy = ensure_empty("Hinge_Green_Yellow")

# ----------------------------------------------------------------------------
# RESET PARENTS / ANIMATION
# ----------------------------------------------------------------------------
for o in [blue, red, green, yellow, hbr, hrg, hgy]:
    clear_anim(o)

for o in [blue, red, green, yellow, hbr, hrg, hgy]:
    clear_parent_keep_world(o)

# ----------------------------------------------------------------------------
# PLACE HINGES FROM CURRENT WORLD POSITIONS
# ----------------------------------------------------------------------------
place_hinge_shared_top_edge(hbr, blue, red)
place_hinge_shared_top_edge(hrg, red, green)
place_hinge_shared_top_edge(hgy, green, yellow)

validate_no_origin_rotation(hbr, hrg)

# ----------------------------------------------------------------------------
# NO-DETACHMENT HIERARCHY
#
# Green side is the stable reference.
# HRG rotates Red+Blue as one attached assembly.
# HBR rotates Blue relative to Red.
# ----------------------------------------------------------------------------
parent_keep_world(hgy, green)
parent_keep_world(yellow, hgy)

parent_keep_world(hrg, green)
parent_keep_world(red, hrg)

parent_keep_world(hbr, red)
parent_keep_world(blue, hbr)

# ----------------------------------------------------------------------------
# CACHE BASE DISTANCES FOR DETACHMENT CHECKS
# ----------------------------------------------------------------------------
dist_blue_red  = (blue.matrix_world.translation - red.matrix_world.translation).length
dist_red_green = (red.matrix_world.translation - green.matrix_world.translation).length

# ----------------------------------------------------------------------------
# KEYFRAMES
# Stage 1: Blue flips first
# Stage 2: Red+Blue move together around HRG
# Stage 3: HRG returns first
# Stage 4: HBR returns second
# ----------------------------------------------------------------------------
scene = bpy.context.scene
scene.frame_start = F1
scene.frame_end   = F240
scene.frame_set(F1)

# HBR
insert_rot_x_deg(hbr, F1,   0.0)
insert_rot_x_deg(hbr, F80,  HBR_SIGN * HBR_DEG)
insert_rot_x_deg(hbr, F81,  HBR_SIGN * HBR_DEG)
insert_rot_x_deg(hbr, F200, HBR_SIGN * HBR_DEG)
insert_rot_x_deg(hbr, F201, HBR_SIGN * HBR_DEG)
insert_rot_x_deg(hbr, F240, 0.0)

# HRG — Z-axis: proven by geometry, Z+90° swings HBR from (0.51,0,1) to (-0.51,0,1)=Green
insert_rot_z_deg(hrg, F1,   0.0)
insert_rot_z_deg(hrg, F80,  0.0)
insert_rot_z_deg(hrg, F81,  0.0)
insert_rot_z_deg(hrg, F160, HRG_SIGN * HRG_DEG)
insert_rot_z_deg(hrg, F161, HRG_SIGN * HRG_DEG)
insert_rot_z_deg(hrg, F200, 0.0)
insert_rot_z_deg(hrg, F240, 0.0)

set_linear(hbr)
set_linear(hrg)

# ----------------------------------------------------------------------------
# QUICK VALIDATION
# ----------------------------------------------------------------------------
for f in [F1, F80, F160, F200, F240]:
    scene.frame_set(f)
    validate_attachment_dist(blue, red, dist_blue_red, "Blue-Red")
    validate_attachment_dist(red, green, dist_red_green, "Red-Green")

scene.frame_set(F1)

print("✓ T04 no-detachment scaffold loaded.")
print("✓ Blue stays attached to Red via Hinge_Blue_Red.")
print("✓ Red stays attached to Green via Hinge_Red_Green.")
print("If motion direction is opposite, flip HRG_SIGN only.")
