import bpy

################################################################################
# SECTION 1: Clear all existing objects
################################################################################
for obj in bpy.data.objects:
    bpy.data.objects.remove(obj, do_unlink=True)

################################################################################
# SECTION 2: Function to create a hollow cube with circular openings
#
# Hole configuration (from original PDF dark bars):
#   Blue   (top-right):  2 holes — top + LEFT side  (faces Yellow across top row)
#   Yellow (top-left):   2 holes — top + RIGHT side (faces Blue across top row)
#   Red    (bottom-right): 1 hole — top only
#   Green  (bottom-left):  1 hole — top only
################################################################################
def create_hollow_cube(location, color, side_hole_direction=None):
    """
    side_hole_direction:
        None       = no side hole (Red, Green)
        'left'     = side hole on LEFT face  (Blue — faces Yellow)
        'right'    = side hole on RIGHT face (Yellow — faces Blue)
    """
    # Adjust location so cube bottom face sits on the ground
    location = (location[0], location[1], location[2] + 0.5)

    # --- Outer cube ---
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    outer_cube = bpy.context.object

    # --- Inner cube for hollow effect ---
    bpy.ops.mesh.primitive_cube_add(size=0.955, location=location)
    inner_cube = bpy.context.object

    bool_mod = outer_cube.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = inner_cube
    bpy.context.view_layer.objects.active = outer_cube
    bpy.ops.object.modifier_apply(modifier="Boolean")
    bpy.data.objects.remove(inner_cube)

    # --- Top hole ---
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.3, depth=0.6,
        location=(location[0], location[1], location[2] + 0.5)
    )
    top_cylinder = bpy.context.object
    # Top cylinder is vertical by default — no rotation needed

    bool_mod_top = outer_cube.modifiers.new(name="Boolean_Top_Hole", type='BOOLEAN')
    bool_mod_top.operation = 'DIFFERENCE'
    bool_mod_top.object = top_cylinder
    bpy.context.view_layer.objects.active = outer_cube
    bpy.ops.object.modifier_apply(modifier="Boolean_Top_Hole")
    bpy.data.objects.remove(top_cylinder)

    # --- Side hole (Blue and Yellow only) ---
    if side_hole_direction == 'left':
        # Blue: side hole on LEFT face (negative X side) — faces Yellow
        side_location = (location[0] - 0.5, location[1], location[2])
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.3, depth=0.6,
            location=side_location
        )
        side_cylinder = bpy.context.object
        side_cylinder.rotation_euler[1] = 1.5708  # Rotate 90° around Y — aligns along X axis

    elif side_hole_direction == 'right':
        # Yellow: side hole on RIGHT face (positive X side) — faces Blue
        side_location = (location[0] + 0.5, location[1], location[2])
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.3, depth=0.6,
            location=side_location
        )
        side_cylinder = bpy.context.object
        side_cylinder.rotation_euler[1] = 1.5708  # Rotate 90° around Y — aligns along X axis

    if side_hole_direction in ('left', 'right'):
        bool_mod_side = outer_cube.modifiers.new(name="Boolean_Side_Hole", type='BOOLEAN')
        bool_mod_side.operation = 'DIFFERENCE'
        bool_mod_side.object = side_cylinder
        bpy.context.view_layer.objects.active = outer_cube
        bpy.ops.object.modifier_apply(modifier="Boolean_Side_Hole")
        bpy.data.objects.remove(side_cylinder)

    # --- Material ---
    mat = bpy.data.materials.new(name="TransparentMaterial")
    mat.diffuse_color = (*color, 0.5)  # RGBA with 50% transparency
    outer_cube.data.materials.append(mat)
    mat.blend_method = 'BLEND'

    return outer_cube

################################################################################
# SECTION 3: Define locations and colors for the four cubes
# Clockwise: Blue (top-right), Red (bottom-right),
#            Green (bottom-left), Yellow (top-left)
################################################################################
locations = [
    (-0.51, -0.51, 0),  # Bottom-left  (Green)
    ( 0.51, -0.51, 0),  # Bottom-right (Red)
    (-0.51,  0.51, 0),  # Top-left     (Yellow)
    ( 0.51,  0.51, 0)   # Top-right    (Blue)
]

blue_color   = (0.0, 0.0, 1.0)  # Blue   — top-right
yellow_color = (1.0, 1.0, 0.0)  # Yellow — top-left
green_color  = (0.0, 1.0, 0.0)  # Green  — bottom-left
red_color    = (1.0, 0.0, 0.0)  # Red    — bottom-right

################################################################################
# SECTION 4: Create the four cubes
#   Blue   (top-right,  x>0, y>0): 2 holes — top + LEFT side  (faces Yellow)
#   Yellow (top-left,   x<0, y>0): 2 holes — top + RIGHT side (faces Blue)
#   Green  (bottom-left,  x<0, y<0): 1 hole — top only
#   Red    (bottom-right, x>0, y<0): 1 hole — top only
################################################################################
cubes = {}
for location in locations:
    if location[0] > 0 and location[1] > 0:       # Blue — top-right
        cubes['blue'] = create_hollow_cube(location, blue_color, side_hole_direction='left')
        cubes['blue'].name = "Cube_Blue"
    elif location[0] < 0 and location[1] > 0:     # Yellow — top-left
        cubes['yellow'] = create_hollow_cube(location, yellow_color, side_hole_direction='right')
        cubes['yellow'].name = "Cube_Yellow"
    elif location[0] < 0 and location[1] < 0:     # Green — bottom-left
        cubes['green'] = create_hollow_cube(location, green_color, side_hole_direction=None)
        cubes['green'].name = "Cube_Green"
    elif location[0] > 0 and location[1] < 0:     # Red — bottom-right
        cubes['red'] = create_hollow_cube(location, red_color, side_hole_direction=None)
        cubes['red'].name = "Cube_Red"

################################################################################
# SECTION 5: Create the ball at the bottom-center of Cube_Blue
# Ball starts inside Blue — first cube in the chain Blue → Red → Green → Yellow
################################################################################
if 'blue' in cubes:
    cube = cubes['blue']
    cube_dimensions = cube.dimensions
    cube_location = cube.location
    ball_radius = 0.25

    bottom_center = (
        cube_location.x,
        cube_location.y,
        cube_location.z - (cube_dimensions.z / 2) + ball_radius * 0.99
    )

    bpy.ops.mesh.primitive_uv_sphere_add(radius=ball_radius, location=bottom_center)
    ball = bpy.context.object
    ball.name = "Ball"

################################################################################
# SECTION 6: Create the 3 hinge pivot empties between cubes
# Chain (clockwise): Blue — Red — Green — Yellow
#
#   Hinge_Blue_Red     : right edge   ( 0.51,  0,    1)
#   Hinge_Red_Green    : bottom edge  ( 0,    -0.51, 1)
#   Hinge_Green_Yellow : left edge    (-0.51,  0,    1)
################################################################################

# Hinge 1: Blue — Red (right edge)
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.51, 0, 1), scale=(0.1, 0.1, 0.1))
hinge_1 = bpy.context.object
hinge_1.name = "Hinge_Blue_Red"

# Hinge 2: Red — Green (bottom edge)
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, -0.51, 1), scale=(0.1, 0.1, 0.1))
hinge_2 = bpy.context.object
hinge_2.name = "Hinge_Red_Green"

# Hinge 3: Green — Yellow (left edge)
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(-0.51, 0, 1), scale=(0.1, 0.1, 0.1))
hinge_3 = bpy.context.object
hinge_3.name = "Hinge_Green_Yellow"

# Hinge 4: Yellow — Blue (top edge)
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0.51, 1), scale=(0.1, 0.1, 0.1))
hinge_4 = bpy.context.object
hinge_4.name = "Hinge_Yellow_Blue"

################################################################################
# SECTION 7: Move each cube's pivot point (origin) to its hinge location
# Ball travel direction: Blue → Red → Green → Yellow
#
#   Blue   pivot → Hinge_Blue_Red     at ( 0.51,  0,    1)
#   Red    pivot → Hinge_Red_Green    at ( 0,    -0.51, 1)
#   Green  pivot → Hinge_Green_Yellow at (-0.51,  0,    1)
#   Yellow pivot → Hinge_Green_Yellow at (-0.51,  0,    1) — free end
################################################################################

# Blue pivot → Hinge_Blue_Red
bpy.context.view_layer.objects.active = cubes['blue']
cubes['blue'].select_set(True)
bpy.context.scene.cursor.location = (0.51, 0, 1)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
cubes['blue'].select_set(False)

# Red pivot → Hinge_Red_Green
bpy.context.view_layer.objects.active = cubes['red']
cubes['red'].select_set(True)
bpy.context.scene.cursor.location = (0, -0.51, 1)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
cubes['red'].select_set(False)

# Green pivot → Hinge_Green_Yellow
bpy.context.view_layer.objects.active = cubes['green']
cubes['green'].select_set(True)
bpy.context.scene.cursor.location = (-0.51, 0, 1)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
cubes['green'].select_set(False)

# Yellow pivot → Hinge_Green_Yellow (free end of chain)
bpy.context.view_layer.objects.active = cubes['yellow']
cubes['yellow'].select_set(True)
bpy.context.scene.cursor.location = (-0.51, 0, 1)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
cubes['yellow'].select_set(False)

print("=== LorQB Scene Setup Complete ===")
print("Chain (clockwise): Blue — Red — Green — Yellow")
print("Blue   (top-right):  2 holes — top + LEFT  side (faces Yellow)")
print("Yellow (top-left):   2 holes — top + RIGHT side (faces Blue)")
print("Red    (bottom-right): 1 hole — top only")
print("Green  (bottom-left):  1 hole — top only")
print("Hinges:")
print("  Hinge_Blue_Red     @ ( 0.51,  0,    1) — right edge")
print("  Hinge_Red_Green    @ ( 0,    -0.51, 1) — bottom edge")
print("  Hinge_Green_Yellow @ (-0.51,  0,    1) — left edge")
print("  Hinge_Yellow_Blue  @ ( 0,     0.51, 1) — top edge")
print("Cube pivots set correctly to their respective hinges.")
