# C10_scene_build.py  — v3  (Blender 5.0.1 — Reset to Base panel added)
import bpy

################################################################################
# SECTION 1: Clear scene helper
################################################################################
def clear_scene():
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    print("=== Scene cleared ===")

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
    mat = bpy.data.materials.new(name=f"Mat_{outer_cube.name}")
    mat.use_nodes = True
    mat.diffuse_color = (*color, 0.35)  # Viewport display color with transparency
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Alpha"].default_value = 0.35
    mat.blend_method = 'HASHED'
    if hasattr(mat, "surface_render_method"):
        try:
            mat.surface_render_method = 'DITHERED'
        except Exception:
            pass
    if hasattr(mat, "shadow_method"):
        try:
            mat.shadow_method = 'NONE'
        except Exception:
            pass
    outer_cube.data.materials.append(mat)

    return outer_cube

################################################################################
# SECTION 3: Build full scene
################################################################################
def build_scene():
    clear_scene()

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

    # ── Ball ────────────────────────────────────────────────────────────────
    if 'blue' in cubes:
        cube            = cubes['blue']
        cube_dimensions = cube.dimensions
        cube_location   = cube.location
        ball_radius     = 0.25

        bottom_center = (
            cube_location.x,
            cube_location.y,
            cube_location.z - (cube_dimensions.z / 2) + ball_radius * 0.99
        )
        bpy.ops.mesh.primitive_uv_sphere_add(radius=ball_radius, location=bottom_center)
        ball = bpy.context.object
        ball.name = "Ball"

    # ── Hinges ──────────────────────────────────────────────────────────────
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.51, 0, 1), scale=(0.1, 0.1, 0.1))
    hinge_1 = bpy.context.object
    hinge_1.name = "Hinge_Blue_Red"

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, -0.51, 1), scale=(0.1, 0.1, 0.1))
    hinge_2 = bpy.context.object
    hinge_2.name = "Hinge_Red_Green"

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(-0.51, 0, 1), scale=(0.1, 0.1, 0.1))
    hinge_3 = bpy.context.object
    hinge_3.name = "Hinge_Green_Yellow"

    # ── Cube pivots → hinge locations ───────────────────────────────────────
    bpy.context.view_layer.objects.active = cubes['blue']
    cubes['blue'].select_set(True)
    bpy.context.scene.cursor.location = (0.51, 0, 1)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    cubes['blue'].select_set(False)

    bpy.context.view_layer.objects.active = cubes['red']
    cubes['red'].select_set(True)
    bpy.context.scene.cursor.location = (0, -0.51, 1)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    cubes['red'].select_set(False)

    bpy.context.view_layer.objects.active = cubes['green']
    cubes['green'].select_set(True)
    bpy.context.scene.cursor.location = (-0.51, 0, 1)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    cubes['green'].select_set(False)

    bpy.context.view_layer.objects.active = cubes['yellow']
    cubes['yellow'].select_set(True)
    bpy.context.scene.cursor.location = (-0.51, 0, 1)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    cubes['yellow'].select_set(False)

    # ── Seats ───────────────────────────────────────────────────────────────
    seat_config = {
        'blue':   ( 0.51,  0.51, 0.0),
        'red':    ( 0.51, -0.51, 0.0),
        'green':  (-0.51, -0.51, 0.0),
        'yellow': (-0.51,  0.51, 0.0),
    }

    seats = {}
    for color_key, seat_loc in seat_config.items():
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=seat_loc, scale=(0.05, 0.05, 0.05))
        seat = bpy.context.object
        seat.name = f"Seat_{color_key.capitalize()}"
        seat.location.x = seat_loc[0]
        seat.location.y = seat_loc[1]
        seat.location.z = seat_loc[2]
        seats[color_key] = seat

    print("Seat empties created:")
    for key, seat in seats.items():
        print(f"  {seat.name} @ {tuple(round(v, 4) for v in seat.location)}")

    # ── Force viewport shading to show material colors ───────────────────────
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type       = 'SOLID'
                    space.shading.color_type = 'MATERIAL'

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
    print("Cube pivots set correctly to their respective hinges.")

################################################################################
# SECTION 4: UI Panel
################################################################################
class LORQB_OT_reset_c10(bpy.types.Operator):
    bl_idname      = "lorqb.reset_c10"
    bl_label       = "Reset to Base"
    bl_description = "Remove all scene objects"

    def execute(self, context):
        clear_scene()
        self.report({'INFO'}, "Scene cleared")
        return {'FINISHED'}


class LORQB_OT_build_c10(bpy.types.Operator):
    bl_idname      = "lorqb.build_c10"
    bl_label       = "Build Scene (C10)"
    bl_description = "Clear and rebuild the full LorQB scene"

    def execute(self, context):
        build_scene()
        self.report({'INFO'}, "Scene built")
        return {'FINISHED'}


class LORQB_PT_c10_panel(bpy.types.Panel):
    bl_label       = "LorQB — C10"
    bl_idname      = "LORQB_PT_c10_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c10", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.build_c10", text="Build Scene (C10)", icon='SCENE_DATA')


_classes = [LORQB_OT_reset_c10, LORQB_OT_build_c10, LORQB_PT_c10_panel]

################################################################################
# SECTION 5: Register / Entry Point
################################################################################
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
build_scene()
